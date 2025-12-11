"""
Upload API Routes.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import shutil
from pathlib import Path

from app.api.deps import get_db
from app.config import settings
from app.schemas.upload import UploadJobResponse, UploadStatus
from app.models.audit import UploadJob
from app.etl.pipeline import run_pipeline

router = APIRouter()


@router.post("/", response_model=UploadJobResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file for processing.
    """
    # Validate extension
    ext = file.filename.split('.')[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}")

    # Create upload record
    job = UploadJob(
        filename=file.filename,
        original_filename=file.filename,
        file_type=ext,
        status="uploaded",
        uploaded_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Save file to disk
    # We use job ID to prevent collisions
    file_path = settings.UPLOAD_DIR / f"{job.id}_{file.filename}"
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Update file path and size
        job.file_path = str(file_path)
        job.file_size = file_path.stat().st_size
        db.commit()
        
    except Exception as e:
        db.delete(job)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    
    # Trigger background ETL
    background_tasks.add_task(run_pipeline, job.id)
    
    return job


@router.get("/{job_id}", response_model=UploadJobResponse)
def get_upload_status(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get status of an upload job."""
    job = db.query(UploadJob).get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")
    return job


@router.get("/history", response_model=list[UploadJobResponse])
def get_upload_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get history of uploads."""
    return db.query(UploadJob).order_by(UploadJob.uploaded_at.desc()).offset(skip).limit(limit).all()
