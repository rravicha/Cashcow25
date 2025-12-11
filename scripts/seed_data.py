"""
Seed the database with initial data.
Adds default categories and institutions.
"""

import sys
import os
from datetime import date

sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.dimensions import InstitutionDim, CategoryDim
from app.api.deps import get_db

def seed_institutions(db):
    """Seed default institutions."""
    institutions = [
        {
            "code": "HDFC",
            "name": "HDFC Bank",
            "type": "bank",
            "short_name": "HDFC"
        },
        {
            "code": "SBI",
            "name": "State Bank of India",
            "type": "bank",
            "short_name": "SBI"
        },
        {
            "code": "ICICI",
            "name": "ICICI Bank",
            "type": "bank",
            "short_name": "ICICI"
        },
        {
            "code": "ZERODHA",
            "name": "Zerodha Broking Ltd",
            "type": "broker",
            "short_name": "Zerodha"
        },
        {
            "code": "CAMS",
            "name": "CAMS",
            "type": "amc",
            "short_name": "CAMS"
        }
    ]
    
    print("Seeding institutions...")
    for inst in institutions:
        exists = db.query(InstitutionDim).filter(InstitutionDim.institution_code == inst["code"]).first()
        if not exists:
            new_inst = InstitutionDim(
                institution_code=inst["code"],
                name=inst["name"],
                institution_type=inst["type"],
                short_name=inst["short_name"],
                is_current=True,
                valid_from=date.today()
            )
            db.add(new_inst)
    db.commit()

def seed_categories(db):
    """Seed default categories."""
    categories = [
        # Income
        {"name": "Salary", "code": "INC_SALARY", "type": "income", "color": "#4CAF50"},
        {"name": "Dividend", "code": "INC_DIV", "type": "income", "color": "#8BC34A"},
        {"name": "Interest", "code": "INC_INT", "type": "income", "color": "#CDDC39"},
        
        # Expenses
        {"name": "Groceries", "code": "EXP_GROCERY", "type": "expense", "color": "#F44336"},
        {"name": "Rent", "code": "EXP_RENT", "type": "expense", "color": "#E91E63"},
        {"name": "Utilities", "code": "EXP_UTIL", "type": "expense", "color": "#9C27B0"},
        {"name": "Travel", "code": "EXP_TRAVEL", "type": "expense", "color": "#673AB7"},
        {"name": "Dining", "code": "EXP_DINING", "type": "expense", "color": "#3F51B5"},
        {"name": "Shopping", "code": "EXP_SHOP", "type": "expense", "color": "#2196F3"},
        {"name": "Medical", "code": "EXP_MED", "type": "expense", "color": "#03A9F4"},
        {"name": "Investment", "code": "EXP_INV", "type": "investment", "color": "#00BCD4"},
        
        # Transfers
        {"name": "Transfer", "code": "TRF_SELF", "type": "transfer", "color": "#607D8B"},
    ]
    
    print("Seeding categories...")
    for cat in categories:
        exists = db.query(CategoryDim).filter(CategoryDim.category_code == cat["code"]).first()
        if not exists:
            new_cat = CategoryDim(
                name=cat["name"],
                category_code=cat["code"],
                category_type=cat["type"],
                color=cat["color"],
                is_current=True,
                valid_from=date.today()
            )
            db.add(new_cat)
    db.commit()

def main():
    db = SessionLocal()
    try:
        seed_institutions(db)
        seed_categories(db)
        print("Database seeded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
