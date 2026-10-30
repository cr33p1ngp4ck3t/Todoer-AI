"""Isolated fixtures: no application database, dotenv secrets, or live providers."""

import os
import socket

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "isolated-test-secret-key"
os.environ["SESSION_SECRET"] = "isolated-test-session-secret"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
for key in (
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "SENTRY_DSN",
):
    os.environ.pop(key, None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402
from src.api.auth import get_password_hash  # noqa: E402
from src.lib import database  # noqa: E402
from src.models.user import User  # noqa: E402
from src.services.task_service import TaskService  # noqa: E402


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail immediately if a test accidentally calls a live service."""
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def connect(sock, address):
        # Asyncio creates loopback sockets internally on Windows.
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original_connect(sock, address)
        raise AssertionError("Live network calls are forbidden in backend tests")

    def connect_ex(sock, address):
        if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return original_connect_ex(sock, address)
        raise AssertionError("Live network calls are forbidden in backend tests")

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)


@pytest.fixture
def db_engine(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(database, "engine", engine)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def test_user(db_session):
    user = User(
        username="tester",
        email="tester@example.com",
        hashed_password=get_password_hash("test-password-123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def task_service(test_user):
    return TaskService(user_id=test_user.id)


@pytest.fixture
def client(db_session):
    from src.main import app

    def get_session():
        yield db_session

    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[database.get_session] = get_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
