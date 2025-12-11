"""
Transaction API Routes.
"""

from typing import List, Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.transaction import (
    TransactionResponse, 
    TransactionFilter, 
    TransactionListResponse,
    TransactionSummary,
    TransactionUpdate
)
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.get("/", response_model=TransactionListResponse)
def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    institution_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    transaction_type: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get transactions with filtering and pagination."""
    service = TransactionService(db)
    
    filters = TransactionFilter(
        account_id=account_id,
        category_id=category_id,
        institution_id=institution_id,
        date_from=date_from,
        date_to=date_to,
        min_amount=min_amount,
        max_amount=max_amount,
        transaction_type=transaction_type,
        search_text=search,
        page=page,
        page_size=page_size
    )
    
    skip = (page - 1) * page_size
    transactions, total_count = service.get_transactions(skip=skip, limit=page_size, filters=filters)
    
    # Calculate simple summary for this view (or fetch separate)
    # For now, let's just make up a summary or fetch global
    # Ideally should be based on current filter
    stats = service.get_summary_stats(date_from=date_from, date_to=date_to)
    
    summary = TransactionSummary(
        total_count=total_count,
        total_credit=stats["total_credit"],
        total_debit=stats["total_debit"],
        net_flow=stats["net_flow"],
        date_from=date_from,
        date_to=date_to
    )
    
    total_pages = (total_count + page_size - 1) // page_size
    
    return TransactionListResponse(
        transactions=transactions,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        summary=summary
    )


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    update_data: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """Update transaction (e.g., category)."""
    service = TransactionService(db)
    updated = service.update_transaction_category(transaction_id, update_data.category_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return updated
