import os

from sqlmodel import SQLModel, create_engine
from src.lib.database_url import use_installed_postgres_driver

# Deprecated: This file is kept for backward compatibility only.
# Use src.lib.database for all session management.

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(
    use_installed_postgres_driver(DATABASE_URL), echo=False, pool_pre_ping=True
)


def init_db():
    """Initialize database tables.

    Deprecated: Use src.lib.database.init_db() instead.
    """
    SQLModel.metadata.create_all(engine)
