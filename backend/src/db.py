from sqlmodel import create_engine, SQLModel
import os

# Deprecated: This file is kept for backward compatibility only.
# Use src.lib.database for all session management.

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


def init_db():
    """Initialize database tables.

    Deprecated: Use src.lib.database.init_db() instead.
    """
    SQLModel.metadata.create_all(engine)
