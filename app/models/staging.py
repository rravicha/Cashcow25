"""
Staging tables for raw parsed data before transformation.
Data is validated and transformed before loading to fact tables.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class BankTransactionStaging(Base):
    """
    Staging table for bank/post office transaction data.
    Raw parsed data before validation and transformation.
    """
    __tablename__ = "stg_bank_transaction"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to upload job
    upload_job_id = Column(Integer, ForeignKey("upload_job.id"), nullable=False)
    
    # Raw parsed fields (as-is from source)
    row_number = Column(Integer)  # Original row in source file
    
    # Date fields (raw strings, parsed later)
    transaction_date_raw = Column(String(100))
    value_date_raw = Column(String(100))
    
    # Parsed dates
    transaction_date = Column(Date)
    value_date = Column(Date)
    
    # Amount fields
    debit_amount = Column(Numeric(18, 2))
    credit_amount = Column(Numeric(18, 2))
    amount = Column(Numeric(18, 2))
    balance = Column(Numeric(18, 2))
    
    # Description
    description = Column(Text)
    reference_number = Column(String(200))
    cheque_number = Column(String(100))
    
    # Account info from file
    account_number_raw = Column(String(200))
    institution_name_raw = Column(String(200))
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, validated, error, processed
    error_message = Column(Text)
    
    # Resolved foreign keys after validation
    account_id = Column(Integer, ForeignKey("dim_account.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("dim_category.id"), nullable=True)
    
    # Computed dedupe key
    dedupe_key = Column(String(255))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    upload_job = relationship("UploadJob", back_populates="bank_staging_records")
    
    def __repr__(self):
        return f"<BankStaging(id={self.id}, date={self.transaction_date}, amount={self.amount})>"


class InvestmentStatementStaging(Base):
    """
    Staging table for investment statement data.
    Handles MF, equity, FD, RD, PPF, NSC statements.
    """
    __tablename__ = "stg_investment_statement"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to upload job
    upload_job_id = Column(Integer, ForeignKey("upload_job.id"), nullable=False)
    
    # Raw parsed fields
    row_number = Column(Integer)
    
    # Statement type
    statement_type = Column(String(50))  # position, transaction, cas
    
    # Date fields
    as_of_date_raw = Column(String(100))
    transaction_date_raw = Column(String(100))
    as_of_date = Column(Date)
    transaction_date = Column(Date)
    
    # Instrument details (raw)
    instrument_type_raw = Column(String(100))
    instrument_name_raw = Column(String(500))
    instrument_code_raw = Column(String(100))
    folio_number_raw = Column(String(200))
    
    # Holdings
    units_raw = Column(String(100))
    nav_raw = Column(String(100))
    units = Column(Numeric(18, 4))
    nav = Column(Numeric(18, 4))
    
    # Values
    invested_value_raw = Column(String(100))
    current_value_raw = Column(String(100))
    invested_value = Column(Numeric(18, 2))
    current_value = Column(Numeric(18, 2))
    
    # For transactions
    transaction_type_raw = Column(String(100))  # purchase, redemption, dividend, sip
    amount_raw = Column(String(100))
    amount = Column(Numeric(18, 2))
    
    # For FD/RD/PPF
    principal_raw = Column(String(100))
    interest_rate_raw = Column(String(100))
    maturity_date_raw = Column(String(100))
    maturity_value_raw = Column(String(100))
    principal = Column(Numeric(18, 2))
    interest_rate = Column(Numeric(8, 4))
    maturity_date = Column(Date)
    maturity_value = Column(Numeric(18, 2))
    
    # Account info from file
    account_number_raw = Column(String(200))
    holder_name_raw = Column(String(300))
    institution_name_raw = Column(String(200))
    
    # Processing status
    status = Column(String(50), default="pending")
    error_message = Column(Text)
    
    # Resolved foreign keys
    account_id = Column(Integer, ForeignKey("dim_account.id"), nullable=True)
    
    # Computed dedupe key
    dedupe_key = Column(String(255))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    upload_job = relationship("UploadJob", back_populates="investment_staging_records")
    
    def __repr__(self):
        return f"<InvestmentStaging(id={self.id}, type={self.statement_type}, instrument={self.instrument_name_raw})>"
