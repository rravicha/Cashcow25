"""
Institution API Routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.account import InstitutionCreate, InstitutionResponse, InstitutionUpdate
from app.services.institution_service import InstitutionService

router = APIRouter()


@router.get("/", response_model=List[InstitutionResponse])
def get_institutions(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all institutions."""
    service = InstitutionService(db)
    return service.get_all_institutions(active_only=active_only)


@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(
    institution_id: int,
    db: Session = Depends(get_db)
):
    """Get institution by ID."""
    service = InstitutionService(db)
    institution = service.get_institution(institution_id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution


@router.post("/", response_model=InstitutionResponse)
def create_institution(
    institution: InstitutionCreate,
    db: Session = Depends(get_db)
):
    """Create a new institution."""
    service = InstitutionService(db)
    # Check if code exists
    existing = service.get_institution_by_code(institution.institution_code)
    if existing:
        raise HTTPException(status_code=400, detail="Institution code already exists")
        
    return service.create_institution(institution)
