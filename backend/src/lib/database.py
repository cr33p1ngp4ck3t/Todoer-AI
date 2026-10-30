import logging
import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine
from src.lib.database_url import use_installed_postgres_driver

# Load environment variables from .env file BEFORE reading DATABASE_URL
load_dotenv()

logger = logging.getLogger("todo-api")

# Database engine - read from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(
    use_installed_postgres_driver(DATABASE_URL), echo=False, pool_pre_ping=True
)


def get_session():
    """Dependency injection for DB sessions.

    Note: This is a regular generator (not async) because SQLModel Session is sync.
    FastAPI can use sync dependencies in async endpoints - it will run them in a threadpool.
    """
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


@contextmanager
def get_session_sync():
    """Synchronous context-manager session for health checks and non-async contexts."""
    with Session(engine) as session:
        yield session


def init_db():
    """Initialize database tables."""
    logger.info("Initializing database...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database initialized successfully")
