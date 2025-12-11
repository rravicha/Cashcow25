"""
Validation Service - Central rules engine for data validation.
Validates parsed data before loading to fact tables.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from app.models.dimensions import InstitutionDim, AccountDim, CategoryDim
from app.models.audit import ErrorLog


class ValidationSeverity(Enum):
    """Validation error severity levels."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_error(self, code: str, message: str, field: str = None, row: int = None):
        """Add an error to the result."""
        self.is_valid = False
        self.errors.append({
            "code": code,
            "message": message,
            "field": field,
            "row": row,
            "severity": ValidationSeverity.ERROR.value
        })
    
    def add_warning(self, code: str, message: str, field: str = None, row: int = None):
        """Add a warning to the result."""
        self.warnings.append({
            "code": code,
            "message": message,
            "field": field,
            "row": row,
            "severity": ValidationSeverity.WARNING.value
        })
    
    def merge(self, other: 'ValidationResult'):
        """Merge another validation result into this one."""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


class ValidationService:
    """
    Central validation service with configurable rules.
    Validates transactions, investments, and other data.
    """
    
    # Validation rules configuration
    RULES = {
        "transaction": {
            "required_fields": ["transaction_date", "amount"],
            "date_range": {"min_years_ago": 10, "max_days_future": 1},
            "amount_range": {"min": Decimal("-1000000000"), "max": Decimal("1000000000")},
        },
        "investment": {
            "required_fields": ["as_of_date", "current_value"],
            "date_range": {"min_years_ago": 50, "max_days_future": 1},
        },
        "account": {
            "required_fields": ["account_number", "account_type"],
            "valid_types": ["savings", "current", "fd", "rd", "ppf", "mf", "equity", "nsc", "sgb"],
        },
        "institution": {
            "required_fields": ["institution_code", "name", "institution_type"],
            "valid_types": ["bank", "post_office", "broker", "amc", "nbfc"],
        }
    }
    
    # Category keywords for auto-categorization
    CATEGORY_KEYWORDS = {
        "salary": ["salary", "payroll", "wages"],
        "rent": ["rent", "rental", "lease"],
        "utilities": ["electricity", "water", "gas", "utility", "broadband", "internet", "mobile"],
        "groceries": ["grocery", "supermarket", "bigbasket", "grofers", "dmart"],
        "food": ["restaurant", "swiggy", "zomato", "food", "cafe", "dining"],
        "transport": ["uber", "ola", "petrol", "diesel", "fuel", "metro", "railway"],
        "shopping": ["amazon", "flipkart", "myntra", "shopping"],
        "healthcare": ["hospital", "medical", "pharmacy", "medicine", "doctor"],
        "insurance": ["lic", "insurance", "premium"],
        "investment": ["sip", "mutual fund", "mf", "investment", "nifty", "sensex"],
        "transfer": ["transfer", "neft", "rtgs", "imps", "upi"],
        "atm": ["atm", "cash withdrawal"],
        "interest": ["interest", "int."],
        "dividend": ["dividend", "div"],
        "emi": ["emi", "loan", "instalment"],
    }
    
    def __init__(self, db: Session):
        """Initialize validation service with database session."""
        self.db = db
    
    def validate_transaction_row(
        self,
        row: Dict[str, Any],
        row_number: int = None
    ) -> ValidationResult:
        """Validate a single transaction row."""
        result = ValidationResult(is_valid=True)
        
        # Required fields
        for field_name in self.RULES["transaction"]["required_fields"]:
            if field_name not in row or row[field_name] is None:
                result.add_error(
                    "REQUIRED_FIELD_MISSING",
                    f"Required field '{field_name}' is missing",
                    field=field_name,
                    row=row_number
                )
        
        # Date validation
        trans_date = row.get("transaction_date")
        if trans_date:
            date_result = self._validate_date(
                trans_date,
                self.RULES["transaction"]["date_range"]["min_years_ago"],
                self.RULES["transaction"]["date_range"]["max_days_future"]
            )
            if not date_result[0]:
                result.add_error("INVALID_DATE", date_result[1], field="transaction_date", row=row_number)
        
        # Amount validation
        amount = row.get("amount") or row.get("debit_amount") or row.get("credit_amount")
        if amount is not None:
            amount_range = self.RULES["transaction"]["amount_range"]
            if amount < amount_range["min"] or amount > amount_range["max"]:
                result.add_warning(
                    "UNUSUAL_AMOUNT",
                    f"Amount {amount} is outside normal range",
                    field="amount",
                    row=row_number
                )
        
        # Description validation
        description = row.get("description")
        if description and len(description) > 1000:
            result.add_warning(
                "LONG_DESCRIPTION",
                "Description exceeds 1000 characters",
                field="description",
                row=row_number
            )
        
        return result
    
    def validate_investment_row(
        self,
        row: Dict[str, Any],
        row_number: int = None
    ) -> ValidationResult:
        """Validate a single investment row."""
        result = ValidationResult(is_valid=True)
        
        # Required fields
        for field_name in self.RULES["investment"]["required_fields"]:
            if field_name not in row or row[field_name] is None:
                result.add_error(
                    "REQUIRED_FIELD_MISSING",
                    f"Required field '{field_name}' is missing",
                    field=field_name,
                    row=row_number
                )
        
        # Date validation
        as_of_date = row.get("as_of_date")
        if as_of_date:
            date_result = self._validate_date(
                as_of_date,
                self.RULES["investment"]["date_range"]["min_years_ago"],
                self.RULES["investment"]["date_range"]["max_days_future"]
            )
            if not date_result[0]:
                result.add_error("INVALID_DATE", date_result[1], field="as_of_date", row=row_number)
        
        # Value validation
        current_value = row.get("current_value")
        if current_value is not None and current_value < 0:
            result.add_warning(
                "NEGATIVE_VALUE",
                f"Current value {current_value} is negative",
                field="current_value",
                row=row_number
            )
        
        # Units/NAV validation
        units = row.get("units")
        nav = row.get("nav")
        if units is not None and nav is not None:
            calculated_value = units * nav
            if current_value and abs(calculated_value - current_value) > Decimal("1"):
                result.add_warning(
                    "VALUE_MISMATCH",
                    f"Calculated value {calculated_value} differs from current value {current_value}",
                    row=row_number
                )
        
        return result
    
    def validate_account(self, account_data: Dict[str, Any]) -> ValidationResult:
        """Validate account data."""
        result = ValidationResult(is_valid=True)
        
        # Required fields
        for field_name in self.RULES["account"]["required_fields"]:
            if field_name not in account_data or not account_data[field_name]:
                result.add_error(
                    "REQUIRED_FIELD_MISSING",
                    f"Required field '{field_name}' is missing",
                    field=field_name
                )
        
        # Account type validation
        account_type = account_data.get("account_type", "").lower()
        if account_type and account_type not in self.RULES["account"]["valid_types"]:
            result.add_warning(
                "UNKNOWN_ACCOUNT_TYPE",
                f"Account type '{account_type}' is not recognized",
                field="account_type"
            )
        
        return result
    
    def validate_institution(self, institution_data: Dict[str, Any]) -> ValidationResult:
        """Validate institution data."""
        result = ValidationResult(is_valid=True)
        
        # Required fields
        for field_name in self.RULES["institution"]["required_fields"]:
            if field_name not in institution_data or not institution_data[field_name]:
                result.add_error(
                    "REQUIRED_FIELD_MISSING",
                    f"Required field '{field_name}' is missing",
                    field=field_name
                )
        
        # Institution type validation
        inst_type = institution_data.get("institution_type", "").lower()
        if inst_type and inst_type not in self.RULES["institution"]["valid_types"]:
            result.add_warning(
                "UNKNOWN_INSTITUTION_TYPE",
                f"Institution type '{inst_type}' is not recognized",
                field="institution_type"
            )
        
        return result
    
    def validate_batch(
        self,
        rows: List[Dict[str, Any]],
        row_type: str = "transaction"
    ) -> Tuple[ValidationResult, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validate a batch of rows.
        
        Returns:
            Tuple of (overall result, valid rows, invalid rows)
        """
        overall_result = ValidationResult(is_valid=True)
        valid_rows = []
        invalid_rows = []
        
        for i, row in enumerate(rows, 1):
            if row_type == "transaction":
                result = self.validate_transaction_row(row, row_number=i)
            elif row_type == "investment":
                result = self.validate_investment_row(row, row_number=i)
            else:
                result = ValidationResult(is_valid=True)
            
            overall_result.merge(result)
            
            if result.is_valid:
                valid_rows.append(row)
            else:
                row["validation_errors"] = result.errors
                invalid_rows.append(row)
        
        return overall_result, valid_rows, invalid_rows
    
    def auto_categorize(self, description: str) -> Optional[str]:
        """
        Auto-categorize a transaction based on description.
        Returns category code or None if no match.
        """
        if not description:
            return None
        
        description_lower = description.lower()
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category
        
        return None
    
    def resolve_account(
        self,
        account_number: str,
        institution_code: str = None
    ) -> Optional[AccountDim]:
        """Resolve account from database by account number."""
        query = self.db.query(AccountDim).filter(
            AccountDim.account_number == account_number,
            AccountDim.is_current == True
        )
        
        if institution_code:
            query = query.join(InstitutionDim).filter(
                InstitutionDim.institution_code == institution_code,
                InstitutionDim.is_current == True
            )
        
        return query.first()
    
    def resolve_category(self, category_code: str) -> Optional[CategoryDim]:
        """Resolve category from database by code."""
        return self.db.query(CategoryDim).filter(
            CategoryDim.category_code == category_code,
            CategoryDim.is_current == True
        ).first()
    
    def log_error(
        self,
        upload_job_id: int,
        error_type: str,
        error_message: str,
        source_row: int = None,
        raw_data: Dict = None,
        severity: str = "error"
    ) -> ErrorLog:
        """Log a validation error to the database."""
        error = ErrorLog(
            upload_job_id=upload_job_id,
            error_type=error_type,
            severity=severity,
            source_row=source_row,
            error_message=error_message,
            raw_data=raw_data
        )
        self.db.add(error)
        return error
    
    def _validate_date(
        self,
        dt: date,
        min_years_ago: int,
        max_days_future: int
    ) -> Tuple[bool, str]:
        """Validate a date is within acceptable range."""
        today = date.today()
        
        min_date = date(today.year - min_years_ago, 1, 1)
        max_date = date.today()
        
        # Allow some future dates for pending transactions
        from datetime import timedelta
        max_date = today + timedelta(days=max_days_future)
        
        if dt < min_date:
            return False, f"Date {dt} is too far in the past (before {min_date})"
        
        if dt > max_date:
            return False, f"Date {dt} is in the future"
        
        return True, ""
