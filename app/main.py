"""
Main Application Entry Point.
Configures FastAPI, middlewares, routes, and serves the web UI.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

from app.config import settings
from app.api import api_router
from app.web import router as web_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Financial Management System",
    debug=settings.DEBUG
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include Web Router (HTML pages) - Must come before API to handle / properly
app.include_router(web_router)

# Include API Router
app.include_router(api_router, prefix="/api")

# Fallback root route
@app.get("/docs", include_in_schema=False)
async def api_docs():
    """API documentation redirect"""
    return RedirectResponse(url="/docs", status_code=307)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
