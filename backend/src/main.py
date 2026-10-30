import logging
import os
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from src.api import chat, conversations, oauth, projects, tasks, token_refresh, users
from src.lib.database import get_session_sync as get_session
from src.lib.database import init_db
from src.lib.logging import JSONFormatter
from starlette.middleware.sessions import SessionMiddleware

# Configure JSON logging
logger = logging.getLogger("todo-api")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    init_db()

    # Validate database connection at startup
    try:
        from src.lib.database import Session, engine

        with Session(engine) as session:
            session.exec(select(1))
        logger.info("Database connection validated successfully")
    except Exception as e:
        logger.error(
            f"Database connection failed at startup: {type(e).__name__}: {e}",
            exc_info=True,
        )
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
    logger.exception("Unhandled request error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
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
app.include_router(projects.router)
app.include_router(users.router)

# Import and include token refresh router
app.include_router(token_refresh.router)

# Import and include OAuth router
app.include_router(oauth.router)

# Import and include Chat router
app.include_router(chat.router)

# Import and include Conversations router
app.include_router(conversations.router)


@app.get("/health")
def health_check():
    """System health check endpoint for K8s probes."""
    readiness = readiness_check()
    if isinstance(readiness, JSONResponse):
        return readiness
    return {"status": "healthy"}


@app.get("/health/ready")
def readiness_check():
    """Readiness check - verify DB connection."""
    try:
        with get_session() as session:
            session.exec(select(1))
        return {"status": "ready"}
    except SQLAlchemyError:
        logger.exception("Readiness check failed")
        return JSONResponse(status_code=503, content={"status": "not_ready"})


@app.get("/health/live")
def liveness_check():
    """Liveness check - service is running."""
    return {"status": "alive"}
