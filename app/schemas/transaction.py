"""Pydantic schemas for transaction-related API operations."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TransactionBase(BaseModel):
    """Base schema for transaction data."""
    transaction_date: date
    value_date: Optional[date] = None
    transaction_type: Optional[str] = None
    amount: Decimal
    balance: Optional[Decimal] = None
    description: Optional[str] = None
    reference_number: Optional[str] = None
    cheque_number: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_account: Optional[str] = None


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    account_id: int
    category_id: Optional[int] = None
    dedupe_key: str


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction (only category can be updated)."""
    category_id: Optional[int] = None
    description: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    category_id: Optional[int] = None
    dedupe_key: str
    source_file: Optional[str] = None
    created_at: datetime
    
    # Joined data
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    institution_name: Optional[str] = None
    category_name: Optional[str] = None


class TransactionFilter(BaseModel):
    """Schema for filtering transactions."""
    account_id: Optional[int] = None
    category_id: Optional[int] = None
    institution_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    search_text: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)


class TransactionSummary(BaseModel):
    """Summary statistics for transactions."""
    total_count: int
    total_credit: Decimal
    total_debit: Decimal
    net_flow: Decimal
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class CategoryBreakdown(BaseModel):
    """Transaction breakdown by category."""
    category_id: Optional[int]
    category_name: str
    transaction_count: int
    total_amount: Decimal
    percentage: float


class MonthlyTrend(BaseModel):
    """Monthly transaction trend data."""
    month: str  # YYYY-MM format
    income: Decimal
    expense: Decimal
    net: Decimal
    transaction_count: int


class TransactionListResponse(BaseModel):
    """Paginated transaction list response."""
    transactions: List[TransactionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    summary: TransactionSummary
