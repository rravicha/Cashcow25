"""Pydantic schemas for category management."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    """Base schema for category data."""
    name: str
    category_code: str
    parent_category: Optional[str] = None
    description: Optional[str] = None
    category_type: Optional[str] = None  # income, expense, transfer, investment
    icon: Optional[str] = None
    color: Optional[str] = None
    keywords: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = None
    parent_category: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    keywords: Optional[str] = None


class CategoryResponse(CategoryBase):
    """Schema for category API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_current: bool
    created_at: datetime
    updated_at: datetime
