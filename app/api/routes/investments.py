"""
Investment API Routes.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.investment import InvestmentPositionResponse, PortfolioSummary, CashFlowResponse
from app.services.investment_service import InvestmentService

router = APIRouter()


@router.get("/portfolio", response_model=PortfolioSummary)
def get_portfolio_summary(
    db: Session = Depends(get_db)
):
    """Get overall portfolio summary."""
    service = InvestmentService(db)
    return service.get_portfolio_summary()


@router.get("/positions", response_model=List[InvestmentPositionResponse])
def get_positions(
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get current investment positions."""
    service = InvestmentService(db)
    return service.get_latest_positions(account_id=account_id)


@router.get("/cash-flows", response_model=List[CashFlowResponse])
def get_cash_flows(
    account_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get investment cash flows."""
    service = InvestmentService(db)
    return service.get_cash_flows(account_id=account_id, limit=limit)
