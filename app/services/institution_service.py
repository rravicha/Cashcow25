"""
Service for managing financial institutions (Banks, Brokers, etc.).
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.dimensions import InstitutionDim
from app.schemas.account import InstitutionCreate, InstitutionUpdate, InstitutionResponse


class InstitutionService:
    def __init__(self, db: Session):
        self.db = db

    def get_institution(self, institution_id: int) -> Optional[InstitutionDim]:
        """Get institution by ID."""
        return self.db.query(InstitutionDim).filter(InstitutionDim.id == institution_id).first()

    def get_institution_by_code(self, code: str) -> Optional[InstitutionDim]:
        """Get current active institution by code."""
        return self.db.query(InstitutionDim).filter(
            InstitutionDim.institution_code == code,
            InstitutionDim.is_current == True
        ).first()

    def get_all_institutions(self, active_only: bool = True) -> List[InstitutionDim]:
        """Get all institutions."""
        query = self.db.query(InstitutionDim)
        if active_only:
            query = query.filter(InstitutionDim.is_current == True)
        return query.all()

    def create_institution(self, institution: InstitutionCreate) -> InstitutionDim:
        """Create a new institution."""
        db_institution = InstitutionDim(
            institution_code=institution.institution_code,
            name=institution.name,
            institution_type=institution.institution_type,
            short_name=institution.short_name,
            website=institution.website,
            contact_info=institution.contact_info,
            is_current=True,
            valid_from=date.today()
        )
        self.db.add(db_institution)
        self.db.commit()
        self.db.refresh(db_institution)
        return db_institution

    # TODO: Implement update with SCD Type 2 logic
    # When updating, we should close the current record and create a new one
