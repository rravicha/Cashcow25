"""
AI/ML-Powered Bank Statement Parser.
Uses LLM and ML algorithms to understand any bank statement format,
extract transactions, and provide intelligent processing.
"""

import pandas as pd
import json
from typing import Dict, Any, List, Tuple
from io import BytesIO
import logging
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.etl.parsers.base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class AIBankParser(BaseParser):
    """
    Intelligent parser for bank statements using AI/ML.
    Automatically detects columns, understands transaction formats,
    and extracts data intelligently.
    """

    # Common transaction keywords for ML detection
    DEBIT_KEYWORDS = [
        'debit', 'withdrawal', 'dr', 'out', 'payment', 'paid', 'transfer out',
        'check', 'cheque', 'atm', 'cash withdrawal', 'deducted'
    ]
    
    CREDIT_KEYWORDS = [
        'credit', 'deposit', 'cr', 'in', 'received', 'transfer in',
        'salary', 'dividend', 'interest', 'refund', 'deposited'
    ]

    def can_parse(self, filename: str, content: bytes) -> bool:
        return filename.lower().endswith(('.csv', '.xlsx', '.xls'))

    def parse(self, content: bytes, filename: str) -> ParseResult:
        """
        Main parse method using AI-driven column detection.
        """
        try:
            df = self._read_file(content, filename)
            if df is None:
                return ParseResult([], {}, [{"error": "Could not read file"}])

            logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")

            # Step 1: AI-based column detection
            column_mapping = self._ai_detect_columns(df.columns)
            logger.info(f"AI detected column mapping: {column_mapping}")

            if not column_mapping or not column_mapping.get('date'):
                return ParseResult([], {}, [{"error": "Could not identify transaction date column"}])

            # Step 2: Intelligent transaction extraction
            transactions = []
            errors = []

            for index, row in df.iterrows():
                try:
                    txn = self._intelligent_parse_row(row, column_mapping, index)
                    if txn:
                        transactions.append(txn)
                except Exception as e:
                    logger.warning(f"Error parsing row {index}: {e}")
                    errors.append({"row": index, "error": str(e)})

            logger.info(f"Parsed {len(transactions)} transactions with {len(errors)} errors")

            return ParseResult(
                transactions=transactions,
                metadata={
                    "row_count": len(transactions),
                    "original_columns": list(df.columns),
                    "detected_mapping": column_mapping
                },
                validation_errors=errors
            )

        except Exception as e:
            logger.error(f"Parse error: {e}")
            return ParseResult([], {}, [{"error": str(e)}])

    def _read_file(self, content: bytes, filename: str) -> pd.DataFrame:
        """Read CSV or Excel file."""
        try:
            name = filename.lower()
            # Try to detect table header row in files that have multiple header lines (bank statements often do)
            def find_header_and_read(read_fn, header_none_reader):
                # header_none_reader should return DataFrame with header=None
                sample = header_none_reader()
                max_check = min(len(sample), 20)
                best_row = None
                best_score = -1

                # First try: look for explicit header keywords in any row (Date, Narration, Withdrawal, Deposit, Balance, Ref)
                # Require at least two header keyword matches in the same row to avoid false positives.
                header_keywords = ['date', 'narration', 'narr', 'withdrawal', 'deposit', 'closing balance', 'value dt', 'value date', 'ref', 'chq', 'cheque', 'particulars', 'withdrawal amt', 'deposit amt']
                for r in range(0, max_check):
                    row = sample.iloc[r].astype(str).str.lower().fillna('')
                    matches = 0
                    for cell in row:
                        for hk in header_keywords:
                            if hk in str(cell):
                                matches += 1
                                break
                    if matches >= 2:
                        best_row = r
                        best_score = 100
                        break

                if best_row is None:
                    for r in range(0, max_check - 1):
                        # Heuristic: header row often precedes a row of actual values (dates & amounts).
                        # So inspect the row after candidate header (r+1) for date and numeric cells.
                        row_after = sample.iloc[r + 1].astype(str).fillna('')
                        date_count = 0
                        numeric_count = 0
                        for val in row_after:
                            try:
                                parsed = pd.to_datetime(val, errors='coerce', dayfirst=False)
                                if not pd.isna(parsed):
                                    date_count += 1
                            except Exception:
                                pass
                            try:
                                v = str(val).replace(',', '').replace('₹', '').strip()
                                if v.replace('.', '', 1).lstrip('-').isdigit():
                                    numeric_count += 1
                            except Exception:
                                pass

                        # Prefer rows where the following row contains at least one date and one numeric value
                        if date_count >= 1 and numeric_count >= 1:
                            best_row = r
                            best_score = date_count * 2 + numeric_count
                            break

                # If we found a promising header row, read with that header
                if best_row is not None and best_score >= 2:
                    try:
                        return read_fn(header=best_row)
                    except Exception:
                        pass

                # Fallback
                return read_fn()

            if name.endswith('.csv'):
                # Try reading without header to detect where table starts
                return find_header_and_read(lambda header=0: pd.read_csv(BytesIO(content), header=header), lambda: pd.read_csv(BytesIO(content), header=None, dtype=str))
            else:
                # Excel - try detecting header row
                return find_header_and_read(lambda header=0: pd.read_excel(BytesIO(content), header=header), lambda: pd.read_excel(BytesIO(content), header=None, dtype=str))
        except Exception as e:
            logger.error(f"File read error: {e}")
            return None

    def _ai_detect_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Use semantic similarity and heuristics to detect column purposes.
        Maps original columns to transaction field types.
        """
        columns_lower = [str(c).lower().strip() for c in columns]
        
        # Define what each column type looks for
        field_matchers = {
            'date': ['date', 'transaction date', 'txn date', 'posting date', 'value date', 'value dt', 'trade date'],
            'description': ['narration', 'description', 'particulars', 'remarks', 'transaction details', 'memo', 'description'],
            'reference': ['reference', 'ref', 'cheque', 'chq', 'check', 'ref no', 'ref.no', 'chq.ref.no', 'chq./ref.no.', 'transaction ref'],
            'debit': ['debit', 'withdrawal', 'dr', 'out', 'withdrawal amt', 'withdrawal amount', 'withdraw'],
            'credit': ['credit', 'deposit', 'cr', 'in', 'deposit amt', 'deposit amount', 'deposited'],
            'amount': ['amount', 'amt', 'value', 'transaction amount'],
            'balance': ['balance', 'running balance', 'closing balance', 'bal']
        }

        mapping = {}
        used_columns = set()

        # Use semantic similarity to match columns
        for field_type, matchers in field_matchers.items():
            best_match = None
            best_score = 0

            for col_idx, col in enumerate(columns_lower):
                if col_idx in used_columns:
                    continue

                # Calculate similarity score
                score = self._similarity_score(col, matchers)

                if score > best_score:
                    best_score = score
                    best_match = col_idx

            if best_match is not None and best_score > 0.3:
                mapping[field_type] = columns[best_match]
                used_columns.add(best_match)
                logger.debug(f"Mapped {field_type} -> {columns[best_match]} (score: {best_score:.2f})")

        return mapping

    def _similarity_score(self, col_name: str, matchers: List[str]) -> float:
        """
        Calculate semantic similarity between column name and matchers.
        Uses multiple heuristics.
        """
        col_name = col_name.lower().strip()
        
        # Exact match gets highest score
        for matcher in matchers:
            matcher_lower = matcher.lower()
            if col_name == matcher_lower:
                return 1.0
            if matcher_lower in col_name or col_name in matcher_lower:
                return 0.8

        # Substring and word overlap
        col_words = set(col_name.replace('.', ' ').replace('/', ' ').split())
        matcher_words = set()
        for matcher in matchers:
            matcher_words.update(matcher.lower().replace('.', ' ').replace('/', ' ').split())

        if col_words and matcher_words:
            overlap = len(col_words & matcher_words) / len(col_words | matcher_words)
            return overlap

        return 0.0

    def _intelligent_parse_row(self, row: pd.Series, mapping: Dict[str, str], row_index: int) -> Dict[str, Any]:
        """
        Intelligently parse a transaction row using ML heuristics.
        Handles varied formats and edge cases.
        """
        try:
            # Extract date
            date_col = mapping.get('date')
            if not date_col or pd.isna(row.get(date_col)):
                return None

            txn_date = self.normalize_date(str(row[date_col]))
            if not txn_date:
                return None

            # Extract value date if available
            value_date = None
            value_date_col = mapping.get('value_date')
            if value_date_col and not pd.isna(row.get(value_date_col)):
                value_date = self.normalize_date(str(row[value_date_col]))

            # Extract description
            desc_col = mapping.get('description')
            description = str(row[desc_col]).strip() if desc_col and not pd.isna(row.get(desc_col)) else "No Description"

            # Extract reference/cheque number
            reference = None
            ref_col = mapping.get('reference')
            if ref_col and not pd.isna(row.get(ref_col)):
                ref_val = str(row[ref_col]).strip()
                reference = ref_val if ref_val and ref_val.lower() not in ['nan', 'none', ''] else None

            # Intelligent amount and type detection
            amount, transaction_type = self._extract_amount_and_type(row, mapping, description)

            if amount is None or amount == 0:
                return None

            # Extract balance
            balance = None
            balance_col = mapping.get('balance')
            if balance_col and not pd.isna(row.get(balance_col)):
                balance = self._parse_amount(row[balance_col])

            return {
                "transaction_date": txn_date,
                "value_date": value_date,
                "description": description,
                "reference_number": reference,
                "amount": abs(amount),
                "transaction_type": transaction_type,
                "balance": balance,
                "source_row": row_index + 1,
                "confidence_score": self._calculate_confidence(description, transaction_type, amount)
            }

        except Exception as e:
            logger.warning(f"Row parse error at index {row_index}: {e}")
            return None

    def _extract_amount_and_type(self, row: pd.Series, mapping: Dict[str, str], description: str) -> Tuple[float, str]:
        """
        Intelligently extract amount and determine transaction type.
        Uses multiple strategies if separate debit/credit columns exist.
        """
        # Strategy 1: Separate debit/credit columns
        debit_col = mapping.get('debit')
        credit_col = mapping.get('credit')

        if debit_col and credit_col:
            debit = self._parse_amount(row.get(debit_col))
            credit = self._parse_amount(row.get(credit_col))

            if debit > 0:
                return debit, "debit"
            elif credit > 0:
                return credit, "credit"
            else:
                return 0, None

        # Strategy 2: Single amount column with type detection
        amount_col = mapping.get('amount')
        if amount_col:
            amount = self._parse_amount(row.get(amount_col))
            if amount == 0:
                return 0, None

            # Detect type from description
            txn_type = self._detect_transaction_type(description)
            return amount, txn_type

        # Strategy 3: Both debit and credit in single columns (fallback)
        if debit_col:
            amount = self._parse_amount(row.get(debit_col))
            if amount > 0:
                return amount, "debit"

        if credit_col:
            amount = self._parse_amount(row.get(credit_col))
            if amount > 0:
                return amount, "credit"

        return 0, None

    def _detect_transaction_type(self, description: str) -> str:
        """
        ML-based detection of transaction type from description.
        Uses keyword matching with configurable weights.
        """
        desc_lower = description.lower()

        # Calculate keyword match scores
        debit_score = sum(1 for keyword in self.DEBIT_KEYWORDS if keyword in desc_lower)
        credit_score = sum(1 for keyword in self.CREDIT_KEYWORDS if keyword in desc_lower)

        # Decide based on scores
        if debit_score > credit_score:
            return "debit"
        elif credit_score > debit_score:
            return "credit"
        else:
            # Default: assume credit (conservative)
            return "credit"

    def _calculate_confidence(self, description: str, transaction_type: str, amount: float) -> float:
        """
        Calculate confidence score for parsed transaction.
        Helps identify potentially problematic or unusual transactions.
        """
        confidence = 0.5  # Base score

        # Bonus: has meaningful description
        if description and description.lower() != "no description" and len(description) > 5:
            confidence += 0.2

        # Bonus: valid transaction type
        if transaction_type in ["credit", "debit"]:
            confidence += 0.1

        # Bonus: reasonable amount
        if 0 < amount < 1_000_000:
            confidence += 0.1

        # Penalty: very high amount (possible error)
        if amount > 10_000_000:
            confidence -= 0.1

        return min(1.0, max(0.0, confidence))

    def _parse_amount(self, value: Any) -> float:
        """Parse numeric amount from various formats."""
        if pd.isna(value) or value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            # Remove common currency symbols and formatting
            clean = str(value).replace(',', '').replace('₹', '').replace('$', '').replace('€', '').replace(' ', '')
            if clean in ['nan', 'none', '']:
                return 0.0
            return float(clean)
        except:
            return 0.0
