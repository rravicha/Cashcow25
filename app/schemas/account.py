"""Pydantic schemas for institution and account management."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class InstitutionBase(BaseModel):
    """Base schema for institution data."""
    institution_code: str
    name: str
    institution_type: str  # bank, post_office, broker, amc
    short_name: Optional[str] = None
    website: Optional[str] = None
    contact_info: Optional[str] = None


class InstitutionCreate(InstitutionBase):
    """Schema for creating a new institution."""
    pass


class InstitutionUpdate(BaseModel):
    """Schema for updating an institution."""
    name: Optional[str] = None
    short_name: Optional[str] = None
    website: Optional[str] = None
    contact_info: Optional[str] = None



class InstitutionResponse(InstitutionBase):
    """Schema for institution API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_current: bool
    created_at: datetime
    updated_at: datetime


class AccountBase(BaseModel):
    """Base schema for account data."""
    account_number: str
    account_name: Optional[str] = None
    account_type: str  # savings, current, fd, rd, ppf, mf, equity
    holder_name: Optional[str] = None
    opening_date: Optional[date] = None
    closing_date: Optional[date] = None
    currency: str = "INR"
    status: str = "active"


class AccountCreate(AccountBase):
    """Schema for creating a new account."""
    institution_id: int


class AccountUpdate(BaseModel):
    """Schema for updating an account."""
    account_name: Optional[str] = None
    holder_name: Optional[str] = None
    status: Optional[str] = None
    closing_date: Optional[date] = None


class AccountResponse(AccountBase):
    """Schema for account API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    institution_id: int
    institution_name: Optional[str] = None  # Joined field
    is_current: bool
    created_at: datetime
    updated_at: datetime
