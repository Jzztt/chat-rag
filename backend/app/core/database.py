"""Database Configuration"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Create database engine with connection pooling optimization
# SQLite specific optimizations
sqlite_connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

if "sqlite" in settings.DATABASE_URL:
    # SQLite optimizations for better performance
    sqlite_connect_args.update({
        "timeout": 20,  # Wait up to 20 seconds for lock
    })
    
    # SQLite WAL mode for better concurrency
    # Note: isolation_level needs to be set differently for SQLite

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=sqlite_connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Max overflow connections
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

