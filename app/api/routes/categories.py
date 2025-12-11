"""
Category API Routes.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    type: Optional[str] = Query(None, description="Filter by category type"),
    db: Session = Depends(get_db)
):
    """Get all categories."""
    service = CategoryService(db)
    return service.get_all_categories(category_type=type)


@router.post("/", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    """Create a new category."""
    service = CategoryService(db)
    # TODO: Check for duplicates by code
    return service.create_category(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category: CategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update a category."""
    service = CategoryService(db)
    updated = service.update_category(category_id, category)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated
