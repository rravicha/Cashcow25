"""
Service for managing investment portfolios.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models.facts import InvestmentPositionFact, CashFlowFact
from app.models.dimensions import AccountDim, InstitutionDim
from app.schemas.investment import PortfolioSummary


class InvestmentService:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_positions(self, account_id: Optional[int] = None) -> List[InvestmentPositionFact]:
        """
        Get the latest positions for each instrument.
        This is tricky with history, usually we filter by max date per instrument
        or just query efficient snapshots.
        For now, let's assume we want positions for the latest 'as_of_date' available in the system
        or per account.
        """
        # First find the latest date
        max_date_query = self.db.query(func.max(InvestmentPositionFact.as_of_date))
        if account_id:
            max_date_query = max_date_query.filter(InvestmentPositionFact.account_id == account_id)
            
        latest_date = max_date_query.scalar()
        
        if not latest_date:
            return []
            
        # Query positions for that date
        query = self.db.query(InvestmentPositionFact).filter(
            InvestmentPositionFact.as_of_date == latest_date
        )
        
        if account_id:
            query = query.filter(InvestmentPositionFact.account_id == account_id)
            
        return query.options(joinedload(InvestmentPositionFact.account).joinedload(AccountDim.institution)).all()

    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get overall portfolio summary."""
        positions = self.get_latest_positions()
        
        total_invested = sum(p.invested_value or 0 for p in positions)
        total_current = sum(p.current_value or 0 for p in positions)
        total_gain = total_current - total_invested
        gain_pct = (total_gain / total_invested * 100) if total_invested else 0
        
        # Calculate allocation
        allocation_map = {}
        for p in positions:
            itype = p.instrument_type
            allocation_map[itype] = allocation_map.get(itype, 0) + (p.current_value or 0)
            
        allocation = [
            {"type": k, "value": v, "percentage": (v / total_current * 100) if total_current else 0}
            for k, v in allocation_map.items()
        ]
        
        return PortfolioSummary(
            total_invested=total_invested,
            total_current=total_current,
            total_gain=total_gain,
            gain_percentage=gain_pct,
            as_of_date=date.today(), # Should be latest date
            asset_allocation=allocation
        )

    def get_cash_flows(self, account_id: Optional[int] = None, limit: int = 50) -> List[CashFlowFact]:
        """Get recent cash flows."""
        query = self.db.query(CashFlowFact)
        if account_id:
            query = query.filter(CashFlowFact.account_id == account_id)
            
        return query.order_by(desc(CashFlowFact.flow_date)).limit(limit).all()
