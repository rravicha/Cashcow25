"""
Database connection and session management for CashCow.
Uses SQLAlchemy for ORM with PostgreSQL backend.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from app.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before use
    echo=settings.DEBUG  # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI to get database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database session.
    Use this in non-FastAPI contexts (background tasks, CLI, tests).
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    # Import all models to ensure they're registered with Base
    from app.models import dimensions, facts, staging, audit  # noqa: F401
    
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    Drop all tables. Use with caution - for testing only.
    """
    Base.metadata.drop_all(bind=engine)


# Event listener for setting search path to configured schema
@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    """Set PostgreSQL search path to configured schema."""
    cursor = dbapi_connection.cursor()
    cursor.execute(f"SET search_path TO {settings.DB_SCHEMA}")
    cursor.close()
