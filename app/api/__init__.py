"""
API Router Aggregator.
Combines all route modules into a single router.
"""

from fastapi import APIRouter

from app.api.routes import (
    institutions,
    accounts,
    categories,
    transactions,
    investments,
    upload
)

api_router = APIRouter()

api_router.include_router(institutions.router, prefix="/institutions", tags=["Institutions"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(investments.router, prefix="/investments", tags=["Investments"])
api_router.include_router(upload.router, prefix="/upload", tags=["Uploads"])
