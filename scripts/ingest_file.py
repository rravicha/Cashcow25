"""
Script to parse and ingest a single bank statement file using the AI parser
and the ETL pipeline. Usage:

  .\cashcow_venv\Scripts\python.exe scripts\ingest_file.py "C:\path\to\Acct_Statement.xls"

The script will:
- Parse the file using `AIBankParser` and print a summary
- Create an UploadJob record in the DB pointing to the file path
- Trigger `run_pipeline(job.id)` to process and insert transactions
- Print final job status and inserted/skipped counts
"""

import sys
import os
from pathlib import Path
import logging

# Ensure repository root is on sys.path so `import app` works when running this script
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from app.database import SessionLocal
from app.models.audit import UploadJob
from app.etl.parsers.ai_parser import AIBankParser
from app.etl.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_upload_job(db, file_path: str, original_filename: str) -> int:
    # `filename` column is required by the DB schema (short/stored name)
    job = UploadJob(
        filename=original_filename,
        original_filename=original_filename,
        file_path=file_path,
        status='pending'
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id


def main():
    if len(sys.argv) < 2:
        print("Usage: ingest_file.py <full-path-to-bank-statement>")
        return 2

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return 3

    filename = Path(file_path).name

    # Step 1: quick parse check
    parser = AIBankParser()
    with open(file_path, 'rb') as f:
        content = f.read()

    if not parser.can_parse(filename, content):
        print("Parser reports: unsupported file type")
        return 4

    result = parser.parse(content, filename)
    print(f"Parser detected {len(result.transactions)} transactions; {len(result.validation_errors)} parse errors")
    print("Detected mapping:", result.metadata.get('detected_mapping'))
    if result.transactions:
        print("Sample parsed transaction:")
        print(result.transactions[0])

    # Step 2: create UploadJob and run pipeline
    db = SessionLocal()
    try:
        job_id = create_upload_job(db, file_path, filename)
        print(f"Created UploadJob {job_id} (file: {filename})")
    finally:
        db.close()

    # Run pipeline (runs in-process; run_pipeline opens its own DB session)
    print("Running ETL pipeline...")
    try:
        run_pipeline(job_id)
    except Exception as e:
        print(f"ETL failed: {e}")
        return 5

    # Inspect job status
    db = SessionLocal()
    try:
        job = db.query(UploadJob).get(job_id)
        print(f"Job {job.id} status: {job.status}")
        print(f"Parsed rows: {job.parsed_rows}, Validated rows: {job.validated_rows}, Processed rows: {job.processed_rows}")
        if job.error_message:
            print("Error message:", job.error_message)
    finally:
        db.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())
