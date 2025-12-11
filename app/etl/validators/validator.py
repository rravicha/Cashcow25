"""
Validation Engine.
Validates parsed data against business rules.
"""

from typing import List, Dict, Any, Optional
from datetime import date

class Validator:
    """
    Validates transactions and other entities.
    """
    
    def validate_transaction(self, txn: Dict[str, Any]) -> List[str]:
        errors = []
        
        # Mandatory fields
        if not txn.get('transaction_date'):
            errors.append("Missing transaction date")
        if txn.get('amount') is None:
            errors.append("Missing amount")
            
        # Logical checks
        if isinstance(txn.get('amount'), (int, float)) and txn['amount'] < 0 and txn.get('transaction_type') != 'debit':
            # This is just a sanity check, amount should ideally be absolute with type
            pass
            
        return errors
    
    def validate_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate a batch of transactions."""
        validation_results = []
        for idx, txn in enumerate(transactions):
            errors = self.validate_transaction(txn)
            if errors:
                validation_results.append({
                    "index": idx,
                    "transaction": txn,
                    "errors": errors
                })
        return validation_results
