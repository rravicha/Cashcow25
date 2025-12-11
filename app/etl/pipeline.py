"""
ETL Pipeline Orchestrator.
Coordinates parsing, validation, transformation, and loading.
Uses AI/ML for intelligent parsing, categorization, and anomaly detection.
"""

import logging
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models.audit import UploadJob, IngestionBatch, AuditLog, ErrorLog
from app.models.facts import TransactionFact
from app.models.dimensions import AccountDim, CategoryDim
from app.etl.parsers.ai_parser import AIBankParser
from app.etl.validators.validator import Validator
from app.etl.transformers.dedupe import DedupeKeyGenerator
from app.etl.transformers.ml_transformers import TransactionCategorizer, AnomalyDetector, DuplicateDetector

logger = logging.getLogger(__name__)


class ETLPipeline:
    def __init__(self, db: Session, user_id: str = "system"):
        self.db = db
        self.user_id = user_id
        self.validator = Validator()
        self.parser = AIBankParser()
        self.categorizer = TransactionCategorizer()
        self.anomaly_detector = AnomalyDetector()
        self.duplicate_detector = DuplicateDetector()

    def process_upload(self, upload_job_id: int):
        """
        Main entry point for processing an upload.
        Uses AI/ML for intelligent parsing and transformation.
        """
        job = self.db.query(UploadJob).get(upload_job_id)
        if not job:
            raise ValueError(f"Upload job {upload_job_id} not found")

        try:
            # 1. Update Status
            logger.info(f"Starting ETL for job {job.id}...")
            print(f"Starting ETL for job {job.id}...")
            job.status = "processing"
            job.processing_started_at = datetime.utcnow()
            self.db.commit()

            # 2. Parse using AI-powered parser
            if not job.file_path:
                raise ValueError("No file path in upload job")

            logger.info(f"Reading file: {job.file_path}")
            print(f"Reading file: {job.file_path}")
            
            with open(job.file_path, "rb") as f:
                content = f.read()

            if not self.parser.can_parse(job.original_filename, content):
                raise ValueError("Unsupported file format")

            # AI-powered parsing
            logger.info("Running AI-powered parser...")
            parse_result = self.parser.parse(content, job.original_filename)
            job.total_rows = parse_result.metadata.get("row_count", 0)
            
            if parse_result.validation_errors:
                logger.warning(f"Parsing errors: {len(parse_result.validation_errors)}")
                print(f"Parsing errors: {len(parse_result.validation_errors)}")
                for err in parse_result.validation_errors:
                    self._log_error(job, "parsing_error", str(err))

            # 3. AI-Based Transformation and Enrichment
            logger.info("Starting AI-based transformation...")
            print("Starting AI-based transformation...")
            
            valid_transactions = []
            
            # Get or identify account
            account = self.db.query(AccountDim).filter_by(is_current=True).first()
            if not account:
                raise ValueError("No accounts configured in system")

            logger.info(f"Mapping to account: {account.account_name} ({account.account_number})")
            print(f"Mapping to account: {account.account_name} ({account.account_number})")
            
            # Train anomaly detector on account's historical transactions
            historical_txns = self.db.query(TransactionFact).filter_by(account_id=account.id).limit(1000).all()
            if historical_txns:
                historical_data = [{
                    'amount': float(t.amount),
                    'transaction_type': t.transaction_type,
                    'transaction_date': t.transaction_date
                } for t in historical_txns]
                self.anomaly_detector.train(historical_data)
                logger.info(f"Trained anomaly detector with {len(historical_data)} historical transactions")
            
            for txn in parse_result.transactions:
                errors = self.validator.validate_transaction(txn)
                if errors:
                    self._log_error(job, "validation_error", f"Row invalid: {errors}", raw=txn)
                    continue
                
                # Assign account
                txn['account_id'] = account.id
                
                # ML: Auto-categorize transaction
                category_name, category_confidence = self.categorizer.categorize(
                    txn.get('description', ''),
                    txn.get('amount', 0),
                    txn.get('transaction_type', 'credit')
                )
                
                # Look up category by name
                category = self.db.query(CategoryDim).filter_by(category_name=category_name).first()
                if category:
                    txn['category_id'] = category.id
                    txn['category_confidence'] = category_confidence
                    logger.debug(f"Categorized as '{category_name}' (confidence: {category_confidence:.2f})")
                
                # ML: Detect anomalies
                is_anomalous, anomaly_score = self.anomaly_detector.detect(txn)
                txn['is_anomalous'] = is_anomalous
                txn['anomaly_score'] = anomaly_score
                
                if is_anomalous:
                    logger.warning(f"Anomaly detected: {txn['description']} - Amount: {txn['amount']} - Score: {anomaly_score:.2f}")
                
                # ML: Check for duplicates
                is_dup, dup_score, matched_txn = self.duplicate_detector.is_duplicate(txn)
                txn['is_duplicate'] = is_dup
                txn['duplicate_score'] = dup_score
                
                # Generate dedupe key
                txn['dedupe_key'] = DedupeKeyGenerator.generate_transaction_key(account.id, txn)
                
                valid_transactions.append(txn)

            job.parsed_rows = len(parse_result.transactions)
            job.validated_rows = len(valid_transactions)
            
            logger.info(f"Validation complete: {len(valid_transactions)} valid transactions")
            print(f"Validation complete: {len(valid_transactions)} valid transactions")

            # 4. Load with ML metadata
            logger.info("Loading transactions with ML enrichment...")
            print("Loading transactions with ML enrichment...")
            
            if valid_transactions:
                batch = IngestionBatch(
                    upload_job_id=job.id,
                    batch_type="transactions",
                    description=f"Import from {job.original_filename} (AI-powered)",
                    status="in_progress",
                    started_at=datetime.utcnow()
                )
                self.db.add(batch)
                self.db.flush()  # get batch ID

                inserted = 0
                skipped = 0
                anomalies = 0
                
                for txn_data in valid_transactions:
                    # Check dedupe
                    exists = self.db.query(TransactionFact).filter_by(dedupe_key=txn_data['dedupe_key']).first()
                    if exists:
                        skipped += 1
                        logger.debug(f"Skipping duplicate: {txn_data['description']}")
                        continue
                    
                    # Track anomalies
                    if txn_data.get('is_anomalous'):
                        anomalies += 1
                        logger.warning(f"Storing anomalous transaction (score: {txn_data.get('anomaly_score'):.2f}): {txn_data['description']}")
                    
                    new_txn = TransactionFact(
                        account_id=txn_data['account_id'],
                        category_id=txn_data.get('category_id'),
                        transaction_date=txn_data['transaction_date'],
                        value_date=txn_data.get('value_date'),
                        transaction_type=txn_data['transaction_type'],
                        amount=txn_data['amount'],
                        description=txn_data['description'],
                        reference_number=txn_data.get('reference_number'),
                        balance=txn_data['balance'],
                        dedupe_key=txn_data['dedupe_key'],
                        source_file=job.original_filename,
                        source_row=txn_data.get('source_row'),
                        batch_id=batch.id
                    )
                    self.db.add(new_txn)
                    inserted += 1

                batch.records_inserted = inserted
                batch.records_skipped = skipped
                batch.status = "committed"
                batch.completed_at = datetime.utcnow()
                
                job.processed_rows = inserted
                
                logger.info(f"Batch complete: Inserted={inserted}, Skipped={skipped}, Anomalies={anomalies}")
                print(f"Batch complete: Inserted={inserted}, Skipped={skipped}, Anomalies={anomalies}")
            
            # 5. Complete job
            job.status = "completed"
            job.processing_completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Job {job.id} completed successfully")
            print(f"Job {job.id} completed successfully")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Job {job.id} failed: {e}", exc_info=True)
            print(f"Job {job.id} failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            self.db.commit()
            raise e

    def _log_error(self, job, error_type, message, raw=None):
        error = ErrorLog(
            upload_job_id=job.id,
            error_type=error_type,
            error_message=message,
            raw_data=raw,
            occurred_at=datetime.utcnow()
        )
        self.db.add(error)

def run_pipeline(upload_job_id: int):
    """Helper to run pipeline in a fresh session."""
    db = SessionLocal()
    try:
        pipeline = ETLPipeline(db)
        pipeline.process_upload(upload_job_id)
    finally:
        db.close()
