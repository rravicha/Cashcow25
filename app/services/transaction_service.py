"""
Service for managing and querying transactions.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models.facts import TransactionFact
from app.models.dimensions import AccountDim, CategoryDim, InstitutionDim
from app.schemas.transaction import TransactionCreate, TransactionFilter, TransactionUpdate


class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def get_transactions(
        self, 
        skip: int = 0, 
        limit: int = 50, 
        filters: Optional[TransactionFilter] = None
    ) -> tuple[List[TransactionFact], int]:
        """
        Get transactions with pagination and filters.
        Returns (transactions, total_count).
        """
        query = self.db.query(TransactionFact).join(TransactionFact.account)
        
        if filters:
            if filters.account_id:
                query = query.filter(TransactionFact.account_id == filters.account_id)
            
            if filters.category_id:
                query = query.filter(TransactionFact.category_id == filters.category_id)
                
            if filters.institution_id:
                query = query.filter(AccountDim.institution_id == filters.institution_id)
                
            if filters.date_from:
                query = query.filter(TransactionFact.transaction_date >= filters.date_from)
                
            if filters.date_to:
                query = query.filter(TransactionFact.transaction_date <= filters.date_to)
                
            if filters.min_amount is not None:
                query = query.filter(TransactionFact.amount >= filters.min_amount)
                
            if filters.max_amount is not None:
                query = query.filter(TransactionFact.amount <= filters.max_amount)
                
            if filters.transaction_type:
                query = query.filter(TransactionFact.transaction_type == filters.transaction_type)
                
            if filters.search_text:
                search = f"%{filters.search_text}%"
                query = query.filter(
                    (TransactionFact.description.ilike(search)) | 
                    (TransactionFact.counterparty_name.ilike(search))
                )

        # distinct count for total
        total_count = query.count()
        
        # Apply sort and pagination
        query = query.order_by(desc(TransactionFact.transaction_date))
        query = query.offset(skip).limit(limit)
        
        # Eager load relationships
        query = query.options(
            joinedload(TransactionFact.account).joinedload(AccountDim.institution),
            joinedload(TransactionFact.category)
        )
        
        return query.all(), total_count

    def get_transaction(self, transaction_id: int) -> Optional[TransactionFact]:
        """Get transaction by ID."""
        return self.db.query(TransactionFact).filter(TransactionFact.id == transaction_id).first()

    def update_transaction_category(self, transaction_id: int, category_id: Optional[int]) -> Optional[TransactionFact]:
        """Update transaction category."""
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            return None
            
        transaction.category_id = category_id
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def get_summary_stats(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> Dict[str, Any]:
        """Get summary statistics for a period."""
        query = self.db.query(
            func.count(TransactionFact.id).label("count"),
            func.sum(TransactionFact.amount).label("total_amount"),
            # You might need more complex logic here for credit/debit separation
            # depending on how amount is stored (signed or unsigned with type column)
        )
        
        # Assuming amount is absolute and we use transaction_type
        # This is a robust way to sum:
        
        credit_query = self.db.query(func.sum(TransactionFact.amount)).filter(TransactionFact.transaction_type == "credit")
        debit_query = self.db.query(func.sum(TransactionFact.amount)).filter(TransactionFact.transaction_type == "debit")
        
        if date_from:
            credit_query = credit_query.filter(TransactionFact.transaction_date >= date_from)
            debit_query = debit_query.filter(TransactionFact.transaction_date >= date_from)
            
        if date_to:
            credit_query = credit_query.filter(TransactionFact.transaction_date <= date_to)
            debit_query = credit_query.filter(TransactionFact.transaction_date <= date_to)
            
        total_credit = credit_query.scalar() or 0
        total_debit = debit_query.scalar() or 0
        
        return {
            "total_credit": total_credit,
            "total_debit": total_debit,
            "net_flow": total_credit - total_debit
        }
