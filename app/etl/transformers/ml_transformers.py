"""
ML-Based Transaction Categorizer and Anomaly Detector.
Automatically categorizes transactions and identifies unusual patterns.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """
    ML-based automatic categorization of transactions.
    Uses description text and amount to assign categories.
    """

    # Default categories and their keywords
    CATEGORY_KEYWORDS = {
        "Salary": ["salary", "wages", "payroll", "stipend", "remuneration"],
        "Groceries": ["grocery", "supermarket", "food", "vegetables", "provisions", "mart", "store"],
        "Utilities": ["electricity", "water", "gas", "internet", "phone", "utility"],
        "Transportation": ["fuel", "petrol", "diesel", "taxi", "uber", "auto", "bus", "metro", "parking"],
        "Healthcare": ["hospital", "doctor", "pharmacy", "medical", "clinic", "health"],
        "Entertainment": ["movie", "cinema", "games", "entertainment", "subscription", "spotify", "netflix"],
        "Insurance": ["insurance", "premium", "policy"],
        "Shopping": ["mall", "shop", "boutique", "apparel", "clothing", "amazon", "flipkart"],
        "Dining": ["restaurant", "cafe", "food delivery", "zomato", "swiggy", "pizza", "burger"],
        "Education": ["school", "college", "tuition", "course", "training", "education"],
        "Rent": ["rent", "landlord", "lease"],
        "Loan": ["loan", "emi", "mortgage", "credit"],
        "Investment": ["investment", "mutual fund", "stock", "trading", "broker"],
        "Transfer": ["transfer", "sent money", "neft", "rtgs", "imps"],
        "Withdrawal": ["atm", "cash withdrawal", "withdrawal"],
        "Other": []
    }

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=100, lowercase=True, stop_words='english')
        self.category_vectors = {}
        self._train_category_model()

    def _train_category_model(self):
        """Train TF-IDF model for category keywords."""
        # Build corpus from category keywords and fit the vectorizer
        corpus = []
        category_texts = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            text = " ".join(keywords) if keywords else ""
            category_texts[category] = text
            corpus.append(text)

        # Ensure there's at least one non-empty document for fitting
        if not any(corpus):
            corpus = ["placeholder"]

        # Fit the vectorizer on the category keyword corpus
        self.vectorizer.fit(corpus)

        # Transform each category to a vector and store
        self.category_vectors = {
            cat: self.vectorizer.transform([text])
            for cat, text in category_texts.items()
        }

    def categorize(self, description: str, amount: float, transaction_type: str) -> Tuple[str, float]:
        """
        Categorize a transaction based on description and amount.
        Returns: (category_name, confidence_score)
        """
        if not description:
            return "Other", 0.0

        description_lower = description.lower()
        best_category = "Other"
        best_score = 0.0

        # Keyword-based matching
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if not keywords:
                continue

            # Calculate match score
            matches = sum(1 for keyword in keywords if keyword in description_lower)
            score = matches / len(keywords) if keywords else 0.0

            if score > best_score:
                best_score = score
                best_category = category

        # Apply heuristics based on transaction type and amount
        if transaction_type == "debit" and best_score < 0.5:
            if amount > 50000:
                best_category = "Transfer"
            elif 100 <= amount <= 500:
                best_category = "Dining"

        # Confidence adjustment
        confidence = min(1.0, best_score + 0.2) if best_score > 0 else 0.3

        return best_category, confidence


class AnomalyDetector:
    """
    ML-based anomaly detection for transactions.
    Identifies unusual patterns and potentially fraudulent transactions.
    """

    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detector.
        contamination: expected proportion of outliers (0.0-1.0)
        """
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False
        self.feature_stats = {}

    def train(self, transactions: List[Dict]) -> bool:
        """
        Train anomaly detector on a set of transactions.
        Transactions should have: amount, transaction_type, day_of_week, etc.
        """
        if not transactions or len(transactions) < 10:
            logger.warning("Insufficient transactions to train anomaly detector")
            return False

        try:
            # Extract features
            features = self._extract_features(transactions)
            
            # Normalize features
            features_normalized = self._normalize_features(features)
            
            # Train model
            self.model.fit(features_normalized)
            self.is_trained = True
            
            logger.info(f"Trained anomaly detector on {len(transactions)} transactions")
            return True

        except Exception as e:
            logger.error(f"Error training anomaly detector: {e}")
            return False

    def detect(self, transaction: Dict) -> Tuple[bool, float]:
        """
        Detect if a transaction is anomalous.
        Returns: (is_anomaly, anomaly_score)
        """
        if not self.is_trained:
            return False, 0.0

        try:
            feature = self._extract_feature_vector(transaction)
            feature_normalized = self._normalize_single_feature(feature)
            
            # Predict (-1 for anomaly, 1 for normal)
            prediction = self.model.predict(feature_normalized.reshape(1, -1))[0]
            # Get anomaly score (lower = more anomalous)
            score = self.model.score_samples(feature_normalized.reshape(1, -1))[0]
            
            is_anomaly = prediction == -1
            # Convert score to 0-1 range (0 = normal, 1 = anomaly)
            anomaly_probability = 1.0 / (1.0 + np.exp(score))
            
            return is_anomaly, anomaly_probability

        except Exception as e:
            logger.error(f"Error detecting anomaly: {e}")
            return False, 0.0

    def _extract_features(self, transactions: List[Dict]) -> np.ndarray:
        """Extract numerical features from transactions."""
        features = []
        
        for txn in transactions:
            feature = self._extract_feature_vector(txn)
            features.append(feature)
        
        return np.array(features)

    def _extract_feature_vector(self, transaction: Dict) -> np.ndarray:
        """Extract individual feature vector from transaction."""
        amount = transaction.get('amount', 0)
        
        # Debit = 1, Credit = 0
        txn_type = 1 if transaction.get('transaction_type') == 'debit' else 0
        
        # Day of week (0-6)
        txn_date = transaction.get('transaction_date')
        day_of_week = txn_date.weekday() if hasattr(txn_date, 'weekday') else 0
        
        # Hour of day (if available, else 12)
        hour = transaction.get('hour', 12)
        
        # Is weekend
        is_weekend = 1 if day_of_week >= 5 else 0
        
        return np.array([
            np.log10(amount + 1),  # Log-scaled amount
            txn_type,
            day_of_week / 7.0,  # Normalized day of week
            hour / 24.0,  # Normalized hour
            is_weekend
        ])

    def _normalize_features(self, features: np.ndarray) -> np.ndarray:
        """Normalize features to mean=0, std=1."""
        # Store stats for future predictions
        self.feature_stats['mean'] = np.mean(features, axis=0)
        self.feature_stats['std'] = np.std(features, axis=0)
        self.feature_stats['std'][self.feature_stats['std'] == 0] = 1  # Avoid division by zero
        
        return (features - self.feature_stats['mean']) / self.feature_stats['std']

    def _normalize_single_feature(self, feature: np.ndarray) -> np.ndarray:
        """Normalize a single feature using trained stats."""
        if not self.feature_stats:
            return feature
        
        return (feature - self.feature_stats['mean']) / self.feature_stats['std']


class DuplicateDetector:
    """
    ML-based duplicate and near-duplicate transaction detection.
    More sophisticated than hash-based deduplication.
    """

    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize duplicate detector.
        similarity_threshold: Jaccard similarity threshold (0.0-1.0)
        """
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3), lowercase=True)
        self.transaction_vectors = {}
        self.known_transactions = {}

    def train(self, transactions: List[Dict]) -> None:
        """Train on known transactions."""
        if not transactions:
            return

        # Store known transactions for reference
        for txn in transactions:
            key = self._create_transaction_key(txn)
            self.known_transactions[key] = txn

    def is_duplicate(self, transaction: Dict) -> Tuple[bool, float, Optional[Dict]]:
        """
        Check if transaction is a duplicate.
        Returns: (is_duplicate, similarity_score, matched_transaction)
        """
        if not self.known_transactions:
            return False, 0.0, None

        txn_key = self._create_transaction_key(transaction)
        
        # Quick check: exact key match
        if txn_key in self.known_transactions:
            return True, 1.0, self.known_transactions[txn_key]

        # Semantic similarity check
        best_match = None
        best_score = 0.0

        for known_key, known_txn in self.known_transactions.items():
            score = self._similarity_score(transaction, known_txn)
            if score > best_score:
                best_score = score
                best_match = known_txn

        is_dup = best_score >= self.similarity_threshold
        return is_dup, best_score, best_match if is_dup else None

    def _create_transaction_key(self, transaction: Dict) -> str:
        """Create a key for fast duplicate lookup."""
        date = transaction.get('transaction_date', '')
        amount = transaction.get('amount', 0)
        desc = transaction.get('description', '')[:50]
        ref = transaction.get('reference_number', '')

        return f"{date}|{amount}|{desc}|{ref}".lower()

    def _similarity_score(self, txn1: Dict, txn2: Dict) -> float:
        """Calculate similarity between two transactions."""
        # Amount similarity (allow 10% variance)
        amt1 = txn1.get('amount', 0)
        amt2 = txn2.get('amount', 0)
        amt_diff = abs(amt1 - amt2) / max(amt1, amt2, 1)
        amt_score = max(0, 1 - amt_diff)

        # Date proximity (allow 2-day window)
        date1 = txn1.get('transaction_date')
        date2 = txn2.get('transaction_date')
        if date1 and date2:
            date_diff = abs((date1 - date2).days)
            date_score = max(0, 1 - (date_diff / 2.0))
        else:
            date_score = 0

        # Description similarity
        desc1 = str(txn1.get('description', '')).lower()
        desc2 = str(txn2.get('description', '')).lower()
        desc_score = self._text_similarity(desc1, desc2)

        # Combined score (weighted)
        combined_score = 0.4 * amt_score + 0.3 * date_score + 0.3 * desc_score
        return combined_score

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between texts."""
        if not text1 or not text2:
            return 0.0

        # Split into n-grams
        ngrams1 = set(self._get_ngrams(text1, 2))
        ngrams2 = set(self._get_ngrams(text2, 2))

        if not ngrams1 or not ngrams2:
            return 0.0

        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)

        return intersection / union if union > 0 else 0.0

    def _get_ngrams(self, text: str, n: int) -> List[str]:
        """Generate n-grams from text."""
        return [text[i:i+n] for i in range(len(text) - n + 1)]
