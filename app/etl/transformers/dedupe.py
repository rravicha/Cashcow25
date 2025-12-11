"""
Deduplication Logic.
Generates deterministic hashes for transactions.
"""

import hashlib
from typing import Dict, Any

class DedupeKeyGenerator:
    """
    Generates deduplication keys.
    """
    
    @staticmethod
    def generate_transaction_key(account_id: int, txn: Dict[str, Any]) -> str:
        """
        Generate a unique hash for a transaction.
        Key = hash(account_id + date + amount + description + type)
        """
        # Normalize fields
        date_str = str(txn.get('transaction_date', ''))
        amount_str = "{:.2f}".format(float(txn.get('amount', 0)))
        desc = txn.get('description', '').strip().lower()[:50] # truncated to reduce noise
        txn_type = txn.get('transaction_type', '')
        
        raw_key = f"{account_id}|{date_str}|{amount_str}|{desc}|{txn_type}"
        
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
