"""
Account API Routes.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.account_service import AccountService
from app.services.institution_service import InstitutionService

router = APIRouter()


@router.get("/", response_model=List[AccountResponse])
def get_accounts(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all accounts."""
    service = AccountService(db)
    # Note: response model will try to map 'institution_name' but model doesn't have it directly.
    # We might need joined loading or map it in service.
    # For now, let's rely on Pydantic's from_attributes and sqlalchemy relationship lazy loading
    # Or eager loading in service (which I added).
    return service.get_accounts(skip=skip, limit=limit, active_only=active_only)


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    """Get account by ID."""
    service = AccountService(db)
    account = service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/", response_model=AccountResponse)
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db)
):
    """Create a new account."""
    acct_service = AccountService(db)
    inst_service = InstitutionService(db)
    
    # Check institution
    inst = inst_service.get_institution(account.institution_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")
        
    # Check duplication
    existing = acct_service.get_account_by_number(account.account_number)
    if existing:
        raise HTTPException(status_code=400, detail="Account number already exists")
        
    return acct_service.create_account(account)
