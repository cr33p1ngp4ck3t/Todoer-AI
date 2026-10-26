from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import select
from src.lib.logging import JSONFormatter
from src.lib.database import init_db, get_session_sync as get_session
from src.api import tasks, users
from starlette.middleware.sessions import SessionMiddleware
import logging
import os
import traceback
import secrets

# Configure JSON logging
logger = logging.getLogger("todo-api")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger().addHandler(handler)  # ADD handler instead of replacing
logging.getLogger().setLevel(logging.DEBUG)  # Enable debug logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    init_db()

    # Validate database connection at startup
    try:
        from src.lib.database import engine, Session

        with Session(engine) as session:
            session.exec(select(1))
        logger.info("Database connection validated successfully")
        print("Database connection validated")  # Visible confirmation
    except Exception as e:
        logger.error(
            f"Database connection failed at startup: {type(e).__name__}: {e}",
            exc_info=True,
        )
        print(f"FATAL: Database connection failed: {e}")
        raise  # Fail fast - don't start server with bad database

    yield


app = FastAPI(title="Todo System API", version="1.0.0", lifespan=lifespan)

# Add SessionMiddleware for OAuth (must be added before other middleware)
# Generate a secret key for session encryption
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to log all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
    )


@app.get("/")
def root():
    """Root endpoint - API information."""
    return {
        "name": "Todo System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# CORS middleware for frontend communication
# Load CORS origins from environment variable (comma-separated)
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
# Parse and strip quotes for robustness
cors_origins_list = [
    origin.strip().replace('"', "") for origin in cors_origins.split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router)
app.include_router(users.router)

# Import and include token refresh router
from src.api import token_refresh

app.include_router(token_refresh.router)

# Import and include OAuth router
from src.api import oauth

app.include_router(oauth.router)

# Import and include Chat router
from src.api import chat

app.include_router(chat.router)

# Import and include Conversations router
from src.api import conversations

app.include_router(conversations.router)


@app.get("/health")
def health_check():
    """System health check endpoint for K8s probes."""
    return {"status": "healthy"}


@app.get("/health/ready")
def readiness_check():
    """Readiness check - verify DB connection."""
    try:
        with get_session() as session:
            session.exec(select(1))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not_ready"}


@app.get("/health/live")
def liveness_check():
    """Liveness check - service is running."""
    return {"status": "alive"}
