import logging
import os
import secrets
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select
from src.api import chat, conversations, oauth, projects, tasks, token_refresh, users
from src.lib.database import get_session_sync as get_session
from src.lib.database import init_db
from src.lib.logging_config import RequestContextMiddleware, setup_logging
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger("todo-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    setup_logging()
    sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            default_integrations=False,
            auto_enabling_integrations=False,
            send_default_pii=False,
            include_local_variables=False,
            environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
            release=os.getenv("SENTRY_RELEASE") or None,
        )
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
    context = getattr(request.state, "log_context", {})
    logger.error(
        "Unhandled request error",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra=context,
    )
    if os.getenv("SENTRY_DSN", "").strip():
        with sentry_sdk.new_scope() as scope:
            scope.set_tag("request_id", context.get("request_id"))
            if context.get("user_id"):
                scope.set_user({"id": context["user_id"]})
            sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers={"X-Request-ID": context["request_id"]} if context else None,
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
    expose_headers=["X-Request-ID"],
)
app.add_middleware(RequestContextMiddleware)

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
