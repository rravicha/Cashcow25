"""
Base Parser Interface.
Defines the contract for all file parsers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from dataclasses import dataclass
from datetime import date
from io import BytesIO
import pandas as pd

@dataclass
class ParseResult:
    """Result of a parsing operation."""
    transactions: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    validation_errors: List[Dict[str, Any]]


class BaseParser(ABC):
    """Abstract base class for parsers."""
    
    @abstractmethod
    def can_parse(self, filename: str, content: bytes) -> bool:
        """Determine if this parser can handle the file."""
        pass

    @abstractmethod
    def parse(self, content: bytes, filename: str) -> ParseResult:
        """Parse the file content into structured data."""
        pass
        
    def normalize_date(self, date_str: str) -> Optional[date]:
        """Helper to normalize date strings."""
        if not date_str:
            return None
        # Add common date parsing logic here using pandas
        try:
            return pd.to_datetime(date_str, dayfirst=True).date()
        except:
            return None
