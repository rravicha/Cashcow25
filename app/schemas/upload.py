"""Pydantic schemas for file upload management."""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, ConfigDict


class UploadStatus(str, Enum):
    """Enum for upload job status."""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    VALIDATING = "validating"
    VALIDATED = "validated"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadJobCreate(BaseModel):
    """Schema for creating a new upload job."""
    filename: str
    file_size: int
    file_type: str
    source_type: Optional[str] = None


class UploadJobResponse(BaseModel):
    """Schema for upload job API response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    filename: str
    original_filename: str
    status: str
    
    source_type: Optional[str] = None
    institution_hint: Optional[str] = None
    
    total_rows: int
    processed_rows: int
    error_rows: int
    
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
