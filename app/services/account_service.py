"""
Service for managing bank and investment accounts.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload

from app.models.dimensions import AccountDim, InstitutionDim
from app.schemas.account import AccountCreate, AccountUpdate


class AccountService:
    def __init__(self, db: Session):
        self.db = db

    def get_account(self, account_id: int) -> Optional[AccountDim]:
        """Get account by ID."""
        return self.db.query(AccountDim).filter(AccountDim.id == account_id).first()

    def get_account_by_number(self, account_number: str) -> Optional[AccountDim]:
        """Get current active account by number."""
        return self.db.query(AccountDim).filter(
            AccountDim.account_number == account_number,
            AccountDim.is_current == True
        ).first()

    def get_accounts(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[AccountDim]:
        """Get all accounts with pagination."""
        query = self.db.query(AccountDim).join(AccountDim.institution)
        
        if active_only:
            query = query.filter(AccountDim.is_current == True)
            
        return query.offset(skip).limit(limit).all()

    def get_accounts_by_institution(self, institution_id: int) -> List[AccountDim]:
        """Get all accounts for an institution."""
        return self.db.query(AccountDim).filter(
            AccountDim.institution_id == institution_id,
            AccountDim.is_current == True
        ).all()

    def create_account(self, account: AccountCreate) -> AccountDim:
        """Create a new account."""
        db_account = AccountDim(
            institution_id=account.institution_id,
            account_number=account.account_number,
            account_name=account.account_name,
            account_type=account.account_type,
            holder_name=account.holder_name,
            opening_date=account.opening_date,
            closing_date=account.closing_date,
            currency=account.currency,
            status=account.status,
            is_current=True,
            valid_from=date.today()
        )
        self.db.add(db_account)
        self.db.commit()
        self.db.refresh(db_account)
        return db_account
