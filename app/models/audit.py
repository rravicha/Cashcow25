"""
Audit and logging tables for tracking uploads, batches, and errors.
Provides complete traceability of all data operations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class UploadJob(Base):
    """
    Upload Job - Tracks each uploaded file and its processing lifecycle.
    """
    __tablename__ = "upload_job"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # File info
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000))
    file_size = Column(Integer)  # bytes
    file_type = Column(String(50))  # pdf, xlsx, csv
    file_hash = Column(String(64))  # SHA-256 for dedup
    
    # Classification
    source_type = Column(String(50))  # bank_statement, mf_cas, fd_statement, etc.
    institution_hint = Column(String(200))  # Detected or user-specified
    
    # Processing status
    status = Column(String(50), default="uploaded")  # uploaded, parsing, parsed, validating, validated, processing, completed, failed
    
    # Statistics
    total_rows = Column(Integer, default=0)
    parsed_rows = Column(Integer, default=0)
    validated_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    
    # Timing
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    parsing_started_at = Column(DateTime)
    parsing_completed_at = Column(DateTime)
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    
    # Error info
    error_message = Column(Text)
    
    # User info (for future multi-user support)
    uploaded_by = Column(String(100))
    
    # Relationships
    bank_staging_records = relationship("BankTransactionStaging", back_populates="upload_job")
    investment_staging_records = relationship("InvestmentStatementStaging", back_populates="upload_job")
    batches = relationship("IngestionBatch", back_populates="upload_job")
    errors = relationship("ErrorLog", back_populates="upload_job")
    
    def __repr__(self):
        return f"<UploadJob(id={self.id}, file={self.original_filename}, status={self.status})>"


class IngestionBatch(Base):
    """
    Ingestion Batch - Groups related loads for rollback and reporting.
    Each batch represents a logical unit of data that was loaded together.
    """
    __tablename__ = "ingestion_batch"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to upload
    upload_job_id = Column(Integer, ForeignKey("upload_job.id"), nullable=True)
    
    # Batch info
    batch_type = Column(String(50))  # transactions, positions, cash_flows
    description = Column(String(500))
    
    # Status
    status = Column(String(50), default="in_progress")  # in_progress, committed, rolled_back
    
    # Statistics
    records_inserted = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)  # Duplicates
    
    # Date range of data
    data_from_date = Column(DateTime)
    data_to_date = Column(DateTime)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    # Relationships
    upload_job = relationship("UploadJob", back_populates="batches")
    transactions = relationship("TransactionFact", back_populates="batch")
    investment_positions = relationship("InvestmentPositionFact", back_populates="batch")
    cash_flows = relationship("CashFlowFact", back_populates="batch")
    audit_logs = relationship("AuditLog", back_populates="batch")
    
    def __repr__(self):
        return f"<IngestionBatch(id={self.id}, type={self.batch_type}, status={self.status})>"


class AuditLog(Base):
    """
    Audit Log - Records every important action for traceability.
    """
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Action details
    action = Column(String(100), nullable=False)  # upload, parse, validate, insert, update, delete, export
    entity_type = Column(String(100))  # transaction, account, institution, etc.
    entity_id = Column(Integer)
    
    # Context
    batch_id = Column(Integer, ForeignKey("ingestion_batch.id"), nullable=True)
    
    # Details
    description = Column(Text)
    old_values = Column(JSON)  # For updates
    new_values = Column(JSON)  # For inserts/updates
    
    # User and timing
    performed_by = Column(String(100))
    performed_at = Column(DateTime, default=datetime.utcnow)
    
    # Request context
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # Relationships
    batch = relationship("IngestionBatch", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, entity={self.entity_type})>"


class ErrorLog(Base):
    """
    Error Log - Captures parsing and validation errors with row context.
    """
    __tablename__ = "error_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to upload
    upload_job_id = Column(Integer, ForeignKey("upload_job.id"), nullable=True)
    
    # Error context
    error_type = Column(String(100), nullable=False)  # parse_error, validation_error, transform_error, load_error
    severity = Column(String(20), default="error")  # warning, error, critical
    
    # Location in source
    source_file = Column(String(500))
    source_sheet = Column(String(200))
    source_row = Column(Integer)
    source_column = Column(String(100))
    
    # Error details
    error_code = Column(String(50))
    error_message = Column(Text, nullable=False)
    error_details = Column(JSON)  # Additional context
    
    # Raw data that caused error
    raw_data = Column(JSON)
    
    # Resolution
    is_resolved = Column(String(10), default="no")  # yes, no, ignored
    resolved_by = Column(String(100))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Timing
    occurred_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    upload_job = relationship("UploadJob", back_populates="errors")
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, type={self.error_type}, row={self.source_row})>"
