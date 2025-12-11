"""
Test and Demo Script for AI/ML-Powered Bank Statement Parser.
Demonstrates intelligent parsing, categorization, and anomaly detection.
"""

import sys
import pandas as pd
from datetime import datetime, timedelta
import json
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add app to path
sys.path.insert(0, '/repo/Cashcow25')

from app.etl.parsers.ai_parser import AIBankParser
from app.etl.transformers.ml_transformers import (
    TransactionCategorizer, AnomalyDetector, DuplicateDetector
)


def create_sample_bank_statement() -> bytes:
    """
    Create a sample bank statement CSV file to test with.
    Mimics real bank statement format.
    """
    data = {
        'Date': [
            '2025-01-05', '2025-01-06', '2025-01-07', '2025-01-08',
            '2025-01-09', '2025-01-10', '2025-01-12', '2025-01-15',
            '2025-01-18', '2025-01-20', '2025-01-22', '2025-01-25'
        ],
        'Narration': [
            'SALARY CREDIT', 'GROCERY MARKET PURCHASE', 'ATM CASH WITHDRAWAL',
            'ELECTRICITY BILL PAYMENT', 'FUEL PETROL PUMP', 'RESTAURANT DINNER',
            'HOSPITAL MEDICAL FEE', 'AMAZON ONLINE PURCHASE', 'MOBILE RECHARGE',
            'INSURANCE PREMIUM', 'SALARY CREDIT', 'UNUSUAL LARGE TRANSFER'
        ],
        'Chq./Ref.No.': [
            '', 'CHQ001', '', 'TRF101', '', '', '', '', '',
            'INS001', '', 'TRF999'
        ],
        'Value Dt': [
            '2025-01-05', '2025-01-06', '2025-01-07', '2025-01-08',
            '2025-01-09', '2025-01-10', '2025-01-12', '2025-01-15',
            '2025-01-18', '2025-01-20', '2025-01-22', '2025-01-25'
        ],
        'Withdrawal Amt.': [
            0, 2500, 5000, 1200, 1500, 800, 2000, 0, 0, 5000, 0, 750000
        ],
        'Deposit Amt.': [
            50000, 0, 0, 0, 0, 0, 0, 3500, 500, 0, 65000, 0
        ],
        'Closing Balance': [
            50000, 47500, 42500, 41300, 39800, 39000, 37000, 40500,
            41000, 36000, 101000, 100250
        ]
    }
    
    df = pd.DataFrame(data)
    csv_bytes = df.to_csv(index=False).encode('utf-8')
    return csv_bytes


def test_ai_parser():
    """Test the AI-powered parser."""
    print("\n" + "="*60)
    print("TEST 1: AI-POWERED PARSER")
    print("="*60)
    
    parser = AIBankParser()
    content = create_sample_bank_statement()
    
    logger.info("Parsing sample bank statement...")
    result = parser.parse(content, "sample_statement.csv")
    
    print(f"\n✓ Parsed {len(result.transactions)} transactions")
    print(f"✓ Detected columns: {result.metadata.get('detected_mapping')}")
    
    if result.validation_errors:
        print(f"⚠ Validation errors: {len(result.validation_errors)}")
        for err in result.validation_errors[:3]:
            print(f"  - {err}")
    
    print("\n--- Sample Transactions ---")
    for txn in result.transactions[:3]:
        print(f"\n  Date: {txn['transaction_date']}")
        print(f"  Description: {txn['description']}")
        print(f"  Type: {txn['transaction_type']}")
        print(f"  Amount: {txn['amount']}")
        print(f"  Reference: {txn.get('reference_number', 'N/A')}")
        print(f"  Confidence: {txn.get('confidence_score', 'N/A'):.2f}")
    
    return result.transactions


def test_categorizer(transactions):
    """Test the transaction categorizer."""
    print("\n" + "="*60)
    print("TEST 2: ML-BASED CATEGORIZATION")
    print("="*60)
    
    categorizer = TransactionCategorizer()
    
    print("\n--- Transaction Categories ---")
    for i, txn in enumerate(transactions[:6], 1):
        category, confidence = categorizer.categorize(
            txn['description'],
            txn['amount'],
            txn['transaction_type']
        )
        print(f"\n  {i}. {txn['description']}")
        print(f"     Category: {category} (confidence: {confidence:.2f})")


def test_anomaly_detector(transactions):
    """Test the anomaly detector."""
    print("\n" + "="*60)
    print("TEST 3: ML-BASED ANOMALY DETECTION")
    print("="*60)
    
    detector = AnomalyDetector(contamination=0.15)
    
    # Train on first 6 transactions
    training_txns = transactions[:6]
    detector.train(training_txns)
    
    print(f"\n✓ Trained on {len(training_txns)} transactions")
    
    print("\n--- Anomaly Scores ---")
    for i, txn in enumerate(transactions, 1):
        is_anomaly, score = detector.detect(txn)
        status = "🚨 ANOMALY" if is_anomaly else "✓ NORMAL"
        print(f"  {i}. {txn['description'][:40]:40} | Amount: ₹{txn['amount']:>10,.0f} | {status} ({score:.2f})")


def test_duplicate_detector(transactions):
    """Test the duplicate detector."""
    print("\n" + "="*60)
    print("TEST 4: ML-BASED DUPLICATE DETECTION")
    print("="*60)
    
    detector = DuplicateDetector(similarity_threshold=0.85)
    
    # Train on all transactions
    detector.train(transactions)
    
    print(f"\n✓ Trained on {len(transactions)} transactions")
    
    # Create a test duplicate
    test_duplicate = {
        'transaction_date': transactions[0]['transaction_date'],
        'amount': transactions[0]['amount'],
        'description': 'SALARY CREDIT (DUPLICATE)',
        'reference_number': transactions[0].get('reference_number')
    }
    
    print("\n--- Testing Duplicate Detection ---")
    is_dup, score, matched = detector.is_duplicate(test_duplicate)
    print(f"\nTest Transaction: {test_duplicate['description']}")
    print(f"  Is Duplicate: {'YES 🚨' if is_dup else 'NO ✓'}")
    print(f"  Similarity Score: {score:.2f}")
    if matched:
        print(f"  Matched with: {matched['description']}")


def generate_report(transactions):
    """Generate a summary report."""
    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    
    total_transactions = len(transactions)
    total_credits = sum(t['amount'] for t in transactions if t['transaction_type'] == 'credit')
    total_debits = sum(t['amount'] for t in transactions if t['transaction_type'] == 'debit')
    avg_amount = (total_credits + total_debits) / total_transactions if total_transactions > 0 else 0
    
    print(f"\n📊 Transaction Summary:")
    print(f"   Total Transactions: {total_transactions}")
    print(f"   Total Credits: ₹{total_credits:,.2f}")
    print(f"   Total Debits: ₹{total_debits:,.2f}")
    print(f"   Net Change: ₹{total_credits - total_debits:,.2f}")
    print(f"   Average Amount: ₹{avg_amount:,.2f}")
    
    # Transaction types
    credits = [t for t in transactions if t['transaction_type'] == 'credit']
    debits = [t for t in transactions if t['transaction_type'] == 'debit']
    
    print(f"\n💰 Transaction Types:")
    print(f"   Credits: {len(credits)} ({len(credits)/total_transactions*100:.1f}%)")
    print(f"   Debits: {len(debits)} ({len(debits)/total_transactions*100:.1f}%)")
    
    # Confidence scores
    avg_confidence = sum(t.get('confidence_score', 0.5) for t in transactions) / total_transactions
    
    print(f"\n🎯 Quality Metrics:")
    print(f"   Average Confidence Score: {avg_confidence:.2f}")
    print(f"   High Confidence (>0.7): {sum(1 for t in transactions if t.get('confidence_score', 0) > 0.7)}")
    print(f"   Medium Confidence (0.5-0.7): {sum(1 for t in transactions if 0.5 <= t.get('confidence_score', 0) <= 0.7)}")
    print(f"   Low Confidence (<0.5): {sum(1 for t in transactions if t.get('confidence_score', 0) < 0.5)}")


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  AI/ML-POWERED BANK STATEMENT PARSER - DEMO  ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        # Test 1: AI Parser
        transactions = test_ai_parser()
        
        # Test 2: Categorizer
        test_categorizer(transactions)
        
        # Test 3: Anomaly Detector
        test_anomaly_detector(transactions)
        
        # Test 4: Duplicate Detector
        test_duplicate_detector(transactions)
        
        # Generate Report
        generate_report(transactions)
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
