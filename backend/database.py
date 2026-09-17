from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from contextlib import contextmanager

from .config import get_settings

settings = get_settings()

# Database engine with connection pooling for production
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.environment == "development",
    pool_pre_ping=True,  # Verify connections before use
    pool_size=5,         # Base connection pool size
    max_overflow=10,     # Additional connections when pool is full
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_timeout=30,     # Timeout for getting connection from pool
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# Import models to register them
from . import models  # noqa: F401


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables (for development only).
    
    In production, use Alembic migrations instead.
    """
    if settings.environment != "production":
        Base.metadata.create_all(bind=engine)
    else:
        # In production, verify tables exist but don't auto-create
        # Use Alembic for migrations: alembic upgrade head
        pass


def check_db_connection() -> bool:
    """Verify database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False