from sqlmodel import Session, create_engine, SQLModel
from contextlib import contextmanager
import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE reading DATABASE_URL
load_dotenv()

logger = logging.getLogger("todo-api")

# Database engine - read from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
print(f">>> DATABASE_URL loaded: {DATABASE_URL[:50]}...")  # Debug: show first 50 chars
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


def get_session():
    """Dependency injection for DB sessions.

    Note: This is a regular generator (not async) because SQLModel Session is sync.
    FastAPI can use sync dependencies in async endpoints - it will run them in a threadpool.
    """
    print(">>> get_session() called - START")  # Entry point
    session = None  # Initialize to None for finally block
    try:
        print(">>> Creating session from engine")
        logger.debug("Creating database session")
        session = Session(engine)  # MOVED INSIDE try block
        print(f">>> Session created successfully: {session}")
        logger.debug("Yielding session to endpoint")
        print(">>> About to yield session")
        yield session
        print(">>> Endpoint finished, committing")
        logger.debug("Committing session")
        session.commit()
        print(">>> Commit successful")
    except Exception as e:
        print(f">>> EXCEPTION CAUGHT: {type(e).__name__}: {e}")
        import traceback

        print(f">>> TRACEBACK:\n{traceback.format_exc()}")
        logger.error(f"Session error: {type(e).__name__}: {e}", exc_info=True)
        print(
            f"CRITICAL ERROR in get_session: {type(e).__name__}: {e}"
        )  # Print for visibility
        if session:
            session.rollback()
        raise  # Re-raise to prevent silent failure
    finally:
        print(">>> get_session() finally block")
        logger.debug("Closing session")
        if session:
            session.close()
            print(">>> Session closed")


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
