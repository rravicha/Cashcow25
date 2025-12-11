"""
Dimension tables with SCD Type 2 support.
These tables track historical changes to master data.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class InstitutionDim(Base):
    """
    Institution Dimension - Banks, post offices, brokers, AMCs.
    Implements SCD Type 2 for tracking historical changes.
    """
    __tablename__ = "dim_institution"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Business Key
    institution_code = Column(String(50), nullable=False, index=True)
    
    # Attributes
    name = Column(String(200), nullable=False)
    institution_type = Column(String(50), nullable=False)  # bank, post_office, broker, amc
    short_name = Column(String(50))
    website = Column(String(200))
    contact_info = Column(String(500))
    
    # SCD Type 2 Fields
    valid_from = Column(Date, nullable=False, default=date.today)
    valid_to = Column(Date, nullable=True)  # NULL means current
    is_current = Column(Boolean, nullable=False, default=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = relationship("AccountDim", back_populates="institution")
    
    # Indexes
    __table_args__ = (
        Index("ix_institution_code_current", "institution_code", "is_current"),
        Index("ix_institution_type", "institution_type"),
    )
    
    def __repr__(self):
        return f"<Institution(id={self.id}, code={self.institution_code}, name={self.name})>"


class AccountDim(Base):
    """
    Account Dimension - Bank, post office, and investment accounts.
    Implements SCD Type 2 for tracking historical changes.
    """
    __tablename__ = "dim_account"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    institution_id = Column(Integer, ForeignKey("dim_institution.id"), nullable=False)
    
    # Business Key
    account_number = Column(String(100), nullable=False, index=True)
    
    # Attributes
    account_name = Column(String(200))
    account_type = Column(String(50), nullable=False)  # savings, current, fd, rd, ppf, mf, equity
    holder_name = Column(String(200))
    opening_date = Column(Date)
    closing_date = Column(Date)
    currency = Column(String(10), default="INR")
    status = Column(String(20), default="active")  # active, closed, dormant
    
    # SCD Type 2 Fields
    valid_from = Column(Date, nullable=False, default=date.today)
    valid_to = Column(Date, nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    institution = relationship("InstitutionDim", back_populates="accounts")
    transactions = relationship("TransactionFact", back_populates="account")
    investment_positions = relationship("InvestmentPositionFact", back_populates="account")
    cash_flows = relationship("CashFlowFact", back_populates="account")
    
    # Indexes
    __table_args__ = (
        Index("ix_account_number_current", "account_number", "is_current"),
        Index("ix_account_institution", "institution_id"),
        Index("ix_account_type", "account_type"),
    )
    
    def __repr__(self):
        return f"<Account(id={self.id}, number={self.account_number}, type={self.account_type})>"


class CategoryDim(Base):
    """
    Category Dimension - Transaction categories for classification.
    Implements SCD Type 2 for tracking historical changes.
    """
    __tablename__ = "dim_category"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Business Key
    category_code = Column(String(50), nullable=False, unique=True, index=True)
    
    # Attributes
    name = Column(String(100), nullable=False)
    parent_category = Column(String(100))  # For hierarchical categories
    description = Column(String(500))
    category_type = Column(String(50))  # income, expense, transfer, investment
    icon = Column(String(50))  # Icon identifier for UI
    color = Column(String(20))  # Color code for UI
    
    # Auto-categorization rules (JSON blob for keywords)
    keywords = Column(String(1000))  # Comma-separated keywords
    
    # SCD Type 2 Fields
    valid_from = Column(Date, nullable=False, default=date.today)
    valid_to = Column(Date, nullable=True)
    is_current = Column(Boolean, nullable=False, default=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("TransactionFact", back_populates="category")
    
    # Indexes
    __table_args__ = (
        Index("ix_category_type", "category_type"),
        Index("ix_category_parent", "parent_category"),
    )
    
    def __repr__(self):
        return f"<Category(id={self.id}, code={self.category_code}, name={self.name})>"
