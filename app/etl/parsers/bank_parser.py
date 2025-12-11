"""
Bank Statement Parser.
Parses CSV/Excel bank statements.
"""

import pandas as pd
from typing import Dict, Any, List
from io import BytesIO
import csv

from app.etl.parsers.base import BaseParser, ParseResult


class BankParser(BaseParser):
    """
    Generic parser for bank statements.
    Currently supports simple CSV/Excel with auto-detection of columns.
    Future: Add specific template logic (HDFC, SBI, etc.)
    """
    
    REQUIRED_COLUMNS = {
        'date': ['date', 'txn date', 'transaction date', 'value date', 'value dt'],
        'value_date': ['value date', 'value dt', 'value_dt'],
        'description': ['narration', 'description', 'particulars', 'remarks'],
        'reference': ['ref', 'cheq', 'chq', 'ref.no', 'chq./ref.no', 'chq/ref', 'cheque ref', 'cheque/ref', 'chq./ref.no.'],
        'debit': ['debit', 'withdrawal', 'withdrawal amt', 'withdrawal amt.', 'dr'],
        'credit': ['credit', 'deposit', 'deposit amt', 'deposit amt.', 'cr'],
        'balance': ['balance', 'bal', 'closing balance', 'closing bal']
    }

    def can_parse(self, filename: str, content: bytes) -> bool:
        return filename.lower().endswith(('.csv', '.xlsx', '.xls'))

    def parse(self, content: bytes, filename: str) -> ParseResult:
        df = self._read_file(content, filename)
        if df is None:
            return ParseResult([], {}, [{"error": "Could not read file"}])
            
        # Normalize columns
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Map columns
        column_map = self._map_columns(df.columns)
        if not column_map.get('date') or (not column_map.get('debit') and not column_map.get('credit') and not column_map.get('amount')):
            return ParseResult([], {}, [{"error": "Could not identify required columns"}])

        transactions = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                txn = self._parse_row(row, column_map)
                if txn:
                    # attach source row (1-based Excel/CSV row number)
                    txn['source_row'] = int(index) + 1
                    transactions.append(txn)
            except Exception as e:
                errors.append({"row": index, "error": str(e)})
                
        return ParseResult(
            transactions=transactions,
            metadata={"row_count": len(transactions), "original_columns": list(df.columns)},
            validation_errors=errors
        )

    def _read_file(self, content: bytes, filename: str) -> pd.DataFrame:
        try:
            if filename.lower().endswith('.csv'):
                return pd.read_csv(BytesIO(content))
            else:
                return pd.read_excel(BytesIO(content))
        except Exception:
            return None

    def _map_columns(self, columns: List[str]) -> Dict[str, str]:
        mapping = {}
        for target, alternatives in self.REQUIRED_COLUMNS.items():
            for col in columns:
                # normalize for lookup
                col_norm = col.replace('.', '').replace('/', ' ').lower()
                if any(alt in col_norm for alt in alternatives):
                    mapping[target] = col
                    break
        
        # Handle 'Amount' column if Debit/Credit separate columns are not found
        if 'debit' not in mapping and 'credit' not in mapping:
             for col in columns:
                 col_norm = col.replace('.', '').replace('/', ' ').lower()
                 if 'amount' in col_norm:
                     mapping['amount'] = col
                     break
                     
        return mapping

    def _parse_row(self, row: pd.Series, mapping: Dict[str, str]) -> Dict[str, Any]:
        # Date
        date_col = mapping.get('date')
        txn_date = self.normalize_date(str(row[date_col])) if date_col else None
        # Value date (optional)
        value_date = None
        if mapping.get('value_date'):
            value_date = self.normalize_date(str(row.get(mapping.get('value_date'))))
        
        if not txn_date:
            return None

        # Amount
        debit = 0.0
        credit = 0.0
        
        if 'debit' in mapping and 'credit' in mapping:
            debit = self._parse_amount(row.get(mapping['debit']))
            credit = self._parse_amount(row.get(mapping['credit']))
        elif 'amount' in mapping:
            amt = self._parse_amount(row.get(mapping['amount']))
            # Heuristic: if description contains 'CR' or 'Credit', or type column says Credit
            if amt < 0:
                debit = abs(amt)
            else:
                credit = amt
                
        amount = credit if credit > 0 else -debit
        txn_type = "credit" if amount > 0 else "debit"
        
        # Description
        desc_col = mapping.get('description')
        description = str(row[desc_col]) if desc_col else "No Description"
        
        # Reference / Cheque number
        reference = None
        if mapping.get('reference'):
            reference = str(row.get(mapping.get('reference')))
        
        return {
            "transaction_date": txn_date,
            "value_date": value_date,
            "description": description,
            "reference_number": reference,
            "amount": abs(amount),
            "transaction_type": txn_type,
            "balance": self._parse_amount(row.get(mapping.get('balance'))) if mapping.get('balance') else None
        }

    def _parse_amount(self, value: Any) -> float:
        if pd.isna(value) or value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        try:
            # Remove symbols
            clean = str(value).replace(',', '').replace('₹', '').replace(' ', '')
            return float(clean)
        except:
            return 0.0
