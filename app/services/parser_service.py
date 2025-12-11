"""
Parser Service - Handles parsing of PDF, Excel, and CSV files.
Extracts structured data from bank and investment statements.
"""

import re
import hashlib
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal, InvalidOperation
import pandas as pd

from app.config import get_settings

settings = get_settings()


class ParserService:
    """
    Service for parsing various file formats into structured data.
    Supports PDF, Excel (xlsx, xls), and CSV files.
    """
    
    # Common date formats in Indian statements
    DATE_FORMATS = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y-%m-%d",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d %b %y",
    ]
    
    # Amount patterns
    AMOUNT_PATTERN = re.compile(r'[\d,]+\.?\d*')
    
    def __init__(self):
        """Initialize parser service."""
        self._pdfplumber = None
        self._tabula = None
    
    @property
    def pdfplumber(self):
        """Lazy load pdfplumber."""
        if self._pdfplumber is None:
            import pdfplumber
            self._pdfplumber = pdfplumber
        return self._pdfplumber
    
    @property
    def tabula(self):
        """Lazy load tabula."""
        if self._tabula is None:
            import tabula
            self._tabula = tabula
        return self._tabula
    
    def get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for deduplication."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def detect_file_type(self, file_path: Path) -> str:
        """Detect file type from extension."""
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            return "pdf"
        elif suffix in [".xlsx", ".xls"]:
            return "excel"
        elif suffix == ".csv":
            return "csv"
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def parse_file(self, file_path: Path, source_type: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parse a file and return structured data.
        
        Args:
            file_path: Path to the file
            source_type: Hint about the source type (bank_statement, mf_cas, etc.)
            
        Returns:
            Tuple of (list of parsed rows, metadata dict)
        """
        file_type = self.detect_file_type(file_path)
        
        if file_type == "pdf":
            return self.parse_pdf(file_path, source_type)
        elif file_type == "excel":
            return self.parse_excel(file_path, source_type)
        elif file_type == "csv":
            return self.parse_csv(file_path, source_type)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def parse_pdf(self, file_path: Path, source_type: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parse PDF file using pdfplumber.
        Falls back to tabula if pdfplumber fails to extract tables.
        """
        rows = []
        metadata = {
            "file_type": "pdf",
            "source_file": str(file_path),
            "parse_method": "pdfplumber"
        }
        
        try:
            with self.pdfplumber.open(file_path) as pdf:
                metadata["page_count"] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if not table or len(table) < 2:
                            continue
                        
                        # First row is typically headers
                        headers = [self._clean_header(h) for h in table[0] if h]
                        
                        for row_num, row in enumerate(table[1:], 2):
                            if not any(row):
                                continue
                            
                            row_dict = {
                                "row_number": len(rows) + 1,
                                "page_number": page_num,
                                "table_index": table_idx,
                                "raw_data": dict(zip(headers, row)) if len(headers) == len(row) else {"values": row}
                            }
                            
                            # Try to extract common fields
                            row_dict.update(self._extract_transaction_fields(row, headers))
                            rows.append(row_dict)
        
        except Exception as e:
            # Fallback to tabula
            metadata["parse_method"] = "tabula"
            metadata["pdfplumber_error"] = str(e)
            
            try:
                dfs = self.tabula.read_pdf(str(file_path), pages='all', multiple_tables=True)
                
                for df_idx, df in enumerate(dfs):
                    if df.empty:
                        continue
                    
                    for idx, row in df.iterrows():
                        row_dict = {
                            "row_number": len(rows) + 1,
                            "table_index": df_idx,
                            "raw_data": row.to_dict()
                        }
                        row_dict.update(self._extract_transaction_fields_from_df_row(row))
                        rows.append(row_dict)
            
            except Exception as tabula_error:
                metadata["tabula_error"] = str(tabula_error)
        
        metadata["total_rows"] = len(rows)
        return rows, metadata
    
    def parse_excel(self, file_path: Path, source_type: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Parse Excel file using pandas."""
        rows = []
        metadata = {
            "file_type": "excel",
            "source_file": str(file_path),
            "parse_method": "pandas"
        }
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            metadata["sheet_names"] = excel_file.sheet_names
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                if df.empty:
                    continue
                
                # Clean column names
                df.columns = [self._clean_header(str(col)) for col in df.columns]
                
                for idx, row in df.iterrows():
                    row_dict = {
                        "row_number": len(rows) + 1,
                        "sheet_name": sheet_name,
                        "excel_row": idx + 2,  # +1 for 0-index, +1 for header
                        "raw_data": {k: v for k, v in row.to_dict().items() if pd.notna(v)}
                    }
                    row_dict.update(self._extract_transaction_fields_from_df_row(row))
                    rows.append(row_dict)
        
        except Exception as e:
            metadata["error"] = str(e)
        
        metadata["total_rows"] = len(rows)
        return rows, metadata
    
    def parse_csv(self, file_path: Path, source_type: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Parse CSV file using pandas."""
        rows = []
        metadata = {
            "file_type": "csv",
            "source_file": str(file_path),
            "parse_method": "pandas"
        }
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    metadata["encoding"] = encoding
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode CSV file with any supported encoding")
            
            if df.empty:
                metadata["total_rows"] = 0
                return rows, metadata
            
            # Clean column names
            df.columns = [self._clean_header(str(col)) for col in df.columns]
            
            for idx, row in df.iterrows():
                row_dict = {
                    "row_number": idx + 2,  # +1 for 0-index, +1 for header
                    "raw_data": {k: v for k, v in row.to_dict().items() if pd.notna(v)}
                }
                row_dict.update(self._extract_transaction_fields_from_df_row(row))
                rows.append(row_dict)
        
        except Exception as e:
            metadata["error"] = str(e)
        
        metadata["total_rows"] = len(rows)
        return rows, metadata
    
    def _clean_header(self, header: str) -> str:
        """Clean and normalize column header."""
        if not header:
            return ""
        # Remove extra whitespace, newlines
        header = re.sub(r'\s+', ' ', str(header)).strip()
        # Convert to lowercase with underscores
        header = re.sub(r'[^\w\s]', '', header)
        header = header.lower().replace(' ', '_')
        return header
    
    def _extract_transaction_fields(self, row: List[Any], headers: List[str]) -> Dict[str, Any]:
        """Extract common transaction fields from a row."""
        result = {}
        
        # Create a dict from row and headers
        row_dict = {}
        for i, header in enumerate(headers):
            if i < len(row):
                row_dict[header.lower()] = row[i]
        
        # Look for date fields
        date_keywords = ['date', 'txn_date', 'transaction_date', 'value_date', 'posting_date']
        for key in date_keywords:
            for header, value in row_dict.items():
                if key in header and value:
                    parsed_date = self._parse_date(str(value))
                    if parsed_date:
                        if 'value' in header:
                            result['value_date_raw'] = str(value)
                            result['value_date'] = parsed_date
                        else:
                            result['transaction_date_raw'] = str(value)
                            result['transaction_date'] = parsed_date
                        break
        
        # Look for amount fields
        amount_keywords = ['amount', 'debit', 'credit', 'withdrawal', 'deposit', 'dr', 'cr']
        for key in amount_keywords:
            for header, value in row_dict.items():
                if key in header and value:
                    amount = self._parse_amount(str(value))
                    if amount is not None:
                        if 'debit' in header or 'withdrawal' in header or header == 'dr':
                            result['debit_amount'] = amount
                        elif 'credit' in header or 'deposit' in header or header == 'cr':
                            result['credit_amount'] = amount
                        else:
                            result['amount'] = amount
        
        # Look for balance
        for header, value in row_dict.items():
            if 'balance' in header and value:
                balance = self._parse_amount(str(value))
                if balance is not None:
                    result['balance'] = balance
                break
        
        # Look for description
        desc_keywords = ['description', 'narration', 'particulars', 'remarks', 'details']
        for key in desc_keywords:
            for header, value in row_dict.items():
                if key in header and value:
                    result['description'] = str(value).strip()
                    break
        
        # Look for reference
        ref_keywords = ['reference', 'ref', 'cheque', 'chq', 'utr']
        for key in ref_keywords:
            for header, value in row_dict.items():
                if key in header and value:
                    if 'cheque' in header or 'chq' in header:
                        result['cheque_number'] = str(value).strip()
                    else:
                        result['reference_number'] = str(value).strip()
        
        return result
    
    def _extract_transaction_fields_from_df_row(self, row: pd.Series) -> Dict[str, Any]:
        """Extract transaction fields from a pandas row."""
        result = {}
        
        for col, value in row.items():
            if pd.isna(value):
                continue
            
            col_lower = str(col).lower()
            value_str = str(value)
            
            # Date fields
            if any(k in col_lower for k in ['date', 'txn', 'posting']):
                parsed_date = self._parse_date(value_str)
                if parsed_date:
                    if 'value' in col_lower:
                        result['value_date_raw'] = value_str
                        result['value_date'] = parsed_date
                    else:
                        result['transaction_date_raw'] = value_str
                        result['transaction_date'] = parsed_date
            
            # Amount fields
            elif any(k in col_lower for k in ['debit', 'withdrawal', 'dr']):
                amount = self._parse_amount(value_str)
                if amount is not None:
                    result['debit_amount'] = amount
            
            elif any(k in col_lower for k in ['credit', 'deposit', 'cr']):
                amount = self._parse_amount(value_str)
                if amount is not None:
                    result['credit_amount'] = amount
            
            elif 'amount' in col_lower:
                amount = self._parse_amount(value_str)
                if amount is not None:
                    result['amount'] = amount
            
            elif 'balance' in col_lower:
                balance = self._parse_amount(value_str)
                if balance is not None:
                    result['balance'] = balance
            
            # Description
            elif any(k in col_lower for k in ['description', 'narration', 'particulars', 'remarks']):
                result['description'] = value_str.strip()
            
            # Reference
            elif any(k in col_lower for k in ['reference', 'ref_no', 'utr']):
                result['reference_number'] = value_str.strip()
            
            elif any(k in col_lower for k in ['cheque', 'chq']):
                result['cheque_number'] = value_str.strip()
        
        return result
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str or pd.isna(date_str):
            return None
        
        date_str = str(date_str).strip()
        
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """Parse amount string to Decimal."""
        if not amount_str or pd.isna(amount_str):
            return None
        
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and whitespace
        amount_str = re.sub(r'[₹$€£\s]', '', amount_str)
        
        # Handle Indian number format (1,23,456.78)
        # Remove commas
        amount_str = amount_str.replace(',', '')
        
        # Handle negative amounts
        is_negative = False
        if amount_str.startswith('-') or amount_str.startswith('('):
            is_negative = True
            amount_str = amount_str.strip('-()').strip()
        
        # Handle Dr/Cr suffix
        if amount_str.lower().endswith('dr'):
            is_negative = True
            amount_str = amount_str[:-2].strip()
        elif amount_str.lower().endswith('cr'):
            amount_str = amount_str[:-2].strip()
        
        try:
            amount = Decimal(amount_str)
            return -amount if is_negative else amount
        except (InvalidOperation, ValueError):
            return None
    
    def generate_dedupe_key(
        self,
        institution_code: str,
        account_number: str,
        transaction_date: date,
        amount: Decimal,
        description: str = ""
    ) -> str:
        """
        Generate a deduplication key for a transaction.
        Uses hash of key fields to create unique identifier.
        """
        key_parts = [
            institution_code.upper(),
            account_number.upper(),
            transaction_date.isoformat(),
            str(amount),
            description[:100] if description else ""
        ]
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
