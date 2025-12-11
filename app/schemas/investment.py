"""Pydantic schemas for investment management."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class InvestmentPositionResponse(BaseModel):
    """Schema for investment position API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    account_number: Optional[str] = None
    institution_name: Optional[str] = None
    
    as_of_date: date
    instrument_type: str
    instrument_name: str
    instrument_code: Optional[str] = None
    
    units: Optional[Decimal] = None
    nav: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None
    
    invested_value: Optional[Decimal] = None
    current_value: Decimal
    unrealized_gain: Optional[Decimal] = None
    
    # FD/RD helpers
    maturity_date: Optional[date] = None
    interest_rate: Optional[Decimal] = None


class CashFlowResponse(BaseModel):
    """Schema for cash flow API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    account_id: int
    flow_date: date
    flow_type: str
    
    instrument_name: Optional[str] = None
    amount: Decimal
    tax_deducted: Optional[Decimal] = None
    
    description: Optional[str] = None


class PortfolioSummary(BaseModel):
    """Schema for portfolio summary statistics."""
    total_invested: Decimal
    total_current: Decimal
    total_gain: Decimal
    gain_percentage: Decimal
    as_of_date: date
    asset_allocation: List[dict]  # {type: str, value: Decimal, percentage: float}
