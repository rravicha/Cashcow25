"""
Web UI Routes.
Handles rendering of HTML templates for the web interface.
Separate from API routes to keep concerns isolated.
"""

from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime, timedelta
import shutil

from app.api.deps import get_db
from app.config import settings
from app.models.audit import UploadJob
from app.models.dimensions import AccountDim, InstitutionDim, CategoryDim
from app.models.facts import TransactionFact
from app.etl.pipeline import run_pipeline
from sqlalchemy import func, desc

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Dashboard home page.
    Shows overview of accounts, recent transactions, and upload statistics.
    """
    try:
        # Get statistics
        total_accounts = db.query(AccountDim).filter(AccountDim.is_current == True).count()
        total_institutions = db.query(InstitutionDim).count()
        total_categories = db.query(CategoryDim).filter(CategoryDim.is_current == True).count()
        
        # Get recent uploads (last 7 days)
        recent_uploads = db.query(UploadJob).order_by(desc(UploadJob.uploaded_at)).limit(5).all()
        
        # Get recent transactions (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_transactions_count = db.query(TransactionFact).filter(
            TransactionFact.created_at >= thirty_days_ago
        ).count()
        
        # Get total transactions
        total_transactions = db.query(TransactionFact).count()
        
        # Get accounts with balances
        accounts = db.query(AccountDim).filter(AccountDim.is_current == True).limit(10).all()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "total_accounts": total_accounts,
            "total_institutions": total_institutions,
            "total_categories": total_categories,
            "total_transactions": total_transactions,
            "recent_transactions_count": recent_transactions_count,
            "recent_uploads": recent_uploads,
            "accounts": accounts,
        })
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error loading dashboard: {str(e)}"
        }, status_code=500)


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Upload file page."""
    return templates.TemplateResponse("upload.html", {"request": request})


@router.post("/upload", response_class=HTMLResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Handle file upload with redirect to status page."""
    try:
        # Validate file was provided
        if not file or not file.filename:
            return templates.TemplateResponse("upload.html", {
                "request": request,
                "error": "Please select a file to upload"
            }, status_code=400)
        
        # Validate extension
        ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if ext not in settings.ALLOWED_EXTENSIONS:
            return templates.TemplateResponse("upload.html", {
                "request": request,
                "error": f"File type not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            }, status_code=400)

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
        file_path = settings.UPLOAD_DIR / f"{job.id}_{file.filename}"
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read file content and save
            content = await file.read()
            with file_path.open("wb") as buffer:
                buffer.write(content)
                
            # Update file path and size
            job.file_path = str(file_path)
            job.file_size = file_path.stat().st_size
            db.commit()
            
        except Exception as e:
            db.delete(job)
            db.commit()
            return templates.TemplateResponse("upload.html", {
                "request": request,
                "error": f"Could not save file: {str(e)}"
            }, status_code=500)
        
        # Trigger background ETL
        background_tasks.add_task(run_pipeline, job.id)
        
        # Redirect to status page
        return RedirectResponse(url=f"/upload/{job.id}", status_code=303)
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": f"Upload error: {str(e)}"
        }, status_code=500)


@router.get("/upload/{job_id}", response_class=HTMLResponse)
async def upload_status(request: Request, job_id: int, db: Session = Depends(get_db)):
    """Show upload status and processing details."""
    job = db.query(UploadJob).filter(UploadJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")
    
    return templates.TemplateResponse("upload_status.html", {
        "request": request,
        "job": job,
    })


@router.get("/uploads", response_class=HTMLResponse)
async def uploads_list(request: Request, db: Session = Depends(get_db)):
    """List all upload jobs."""
    uploads = db.query(UploadJob).order_by(desc(UploadJob.uploaded_at)).all()
    
    return templates.TemplateResponse("uploads_list.html", {
        "request": request,
        "uploads": uploads,
    })


@router.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request, db: Session = Depends(get_db)):
    """List all accounts."""
    accounts = db.query(AccountDim).filter(AccountDim.is_current == True).all()
    
    return templates.TemplateResponse("accounts.html", {
        "request": request,
        "accounts": accounts,
    })


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request,
    page: int = 1,
    account_id: int = None,
    db: Session = Depends(get_db)
):
    """List transactions with pagination and filtering."""
    page_size = 50
    skip = (page - 1) * page_size
    
    query = db.query(TransactionFact)
    
    if account_id:
        query = query.filter(TransactionFact.account_id == account_id)
    
    total_count = query.count()
    transactions = query.order_by(desc(TransactionFact.transaction_date)).offset(skip).limit(page_size).all()
    
    total_pages = (total_count + page_size - 1) // page_size
    accounts = db.query(AccountDim).filter(AccountDim.is_current == True).all()
    
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "transactions": transactions,
        "accounts": accounts,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "account_id": account_id,
    })


@router.get("/institutions", response_class=HTMLResponse)
async def institutions_page(request: Request, db: Session = Depends(get_db)):
    """List all institutions."""
    institutions = db.query(InstitutionDim).all()
    
    return templates.TemplateResponse("institutions.html", {
        "request": request,
        "institutions": institutions,
    })


@router.get("/categories", response_class=HTMLResponse)
async def categories_page(request: Request, db: Session = Depends(get_db)):
    """List all categories."""
    categories = db.query(CategoryDim).all()
    
    return templates.TemplateResponse("categories.html", {
        "request": request,
        "categories": categories,
    })
