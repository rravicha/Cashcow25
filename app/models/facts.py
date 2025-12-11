"""
Fact tables for transactions, investments, and cash flows.
These are immutable ledgers capturing financial events.
"""

from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TransactionFact(Base):
    """
    Transaction Fact - Immutable ledger of all financial transactions.
    Each row represents a single transaction from bank/post office statements.
    """
    __tablename__ = "fact_transaction"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    account_id = Column(Integer, ForeignKey("dim_account.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("dim_category.id"), nullable=True)
    batch_id = Column(Integer, ForeignKey("ingestion_batch.id"), nullable=True)
    
    # Transaction Details
    transaction_date = Column(Date, nullable=False)
    value_date = Column(Date)  # Settlement date
    transaction_type = Column(String(50))  # credit, debit
    amount = Column(Numeric(18, 2), nullable=False)
    balance = Column(Numeric(18, 2))  # Running balance after transaction
    
    # Description
    description = Column(Text)
    reference_number = Column(String(100))
    cheque_number = Column(String(50))
    
    # Counterparty
    counterparty_name = Column(String(200))
    counterparty_account = Column(String(100))
    
    # Deduplication
    dedupe_key = Column(String(255), nullable=False, unique=True, index=True)
    
    # Source tracking
    source_file = Column(String(500))
    source_row = Column(Integer)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("AccountDim", back_populates="transactions")
    category = relationship("CategoryDim", back_populates="transactions")
    batch = relationship("IngestionBatch", back_populates="transactions")
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_transaction_account_date", "account_id", "transaction_date"),
        Index("ix_transaction_date", "transaction_date"),
        Index("ix_transaction_category", "category_id"),
        Index("ix_transaction_type", "transaction_type"),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, date={self.transaction_date}, amount={self.amount})>"


class InvestmentPositionFact(Base):
    """
    Investment Position Fact - Snapshot of investment holdings.
    Captures positions in MF, equity, FD, RD, PPF, NSC, etc.
    """
    __tablename__ = "fact_investment_position"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    account_id = Column(Integer, ForeignKey("dim_account.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("ingestion_batch.id"), nullable=True)
    
    # Position Date
    as_of_date = Column(Date, nullable=False)
    
    # Instrument Details
    instrument_type = Column(String(50), nullable=False)  # mf, equity, fd, rd, ppf, nsc, sgb
    instrument_name = Column(String(200), nullable=False)
    instrument_code = Column(String(50))  # ISIN, scheme code, etc.
    
    # Holdings
    units = Column(Numeric(18, 4))  # For MF/equity
    nav = Column(Numeric(18, 4))  # Net Asset Value
    average_cost = Column(Numeric(18, 4))  # Average purchase price
    
    # Values
    invested_value = Column(Numeric(18, 2))  # Total amount invested
    current_value = Column(Numeric(18, 2), nullable=False)
    unrealized_gain = Column(Numeric(18, 2))
    
    # For FD/RD/PPF
    principal = Column(Numeric(18, 2))
    interest_rate = Column(Numeric(8, 4))
    maturity_date = Column(Date)
    maturity_value = Column(Numeric(18, 2))
    
    # Deduplication
    dedupe_key = Column(String(255), nullable=False, unique=True, index=True)
    
    # Source tracking
    source_file = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("AccountDim", back_populates="investment_positions")
    batch = relationship("IngestionBatch", back_populates="investment_positions")
    
    # Indexes
    __table_args__ = (
        Index("ix_position_account_date", "account_id", "as_of_date"),
        Index("ix_position_instrument", "instrument_type", "instrument_code"),
        Index("ix_position_date", "as_of_date"),
    )
    
    def __repr__(self):
        return f"<InvestmentPosition(id={self.id}, instrument={self.instrument_name}, value={self.current_value})>"


class CashFlowFact(Base):
    """
    Cash Flow Fact - Cash flows for investment accounts.
    Tracks purchases, redemptions, dividends, interest, etc.
    """
    __tablename__ = "fact_cash_flow"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    account_id = Column(Integer, ForeignKey("dim_account.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("ingestion_batch.id"), nullable=True)
    
    # Flow Details
    flow_date = Column(Date, nullable=False)
    flow_type = Column(String(50), nullable=False)  # purchase, redemption, dividend, interest, sip, switch_in, switch_out
    
    # Instrument
    instrument_type = Column(String(50))
    instrument_name = Column(String(200))
    instrument_code = Column(String(50))
    
    # Transaction details
    units = Column(Numeric(18, 4))
    nav = Column(Numeric(18, 4))
    amount = Column(Numeric(18, 2), nullable=False)
    
    # Tax
    tax_deducted = Column(Numeric(18, 2), default=0)
    
    # Description
    description = Column(Text)
    folio_number = Column(String(100))
    
    # Deduplication
    dedupe_key = Column(String(255), nullable=False, unique=True, index=True)
    
    # Source tracking
    source_file = Column(String(500))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("AccountDim", back_populates="cash_flows")
    batch = relationship("IngestionBatch", back_populates="cash_flows")
    
    # Indexes
    __table_args__ = (
        Index("ix_cashflow_account_date", "account_id", "flow_date"),
        Index("ix_cashflow_type", "flow_type"),
        Index("ix_cashflow_date", "flow_date"),
    )
    
    def __repr__(self):
        return f"<CashFlow(id={self.id}, type={self.flow_type}, amount={self.amount})>"
