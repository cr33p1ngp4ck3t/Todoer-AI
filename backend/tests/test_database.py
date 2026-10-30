import importlib

import pytest
from sqlmodel import Session
from src.lib.database import get_session
from src.models.user import User


@pytest.mark.parametrize("module_name", ["src.lib.database", "src.db"])
@pytest.mark.parametrize(
    "url, driver",
    [
        ("postgresql://todo:disposable@localhost/todo?sslmode=require", "psycopg2"),
        ("postgresql+psycopg2://todo:disposable@localhost/todo", "psycopg2"),
        ("sqlite://", "pysqlite"),
    ],
)
def test_database_startup_uses_installed_driver(monkeypatch, module_name, url, driver):
    module = importlib.import_module(module_name)
    monkeypatch.setenv("DATABASE_URL", url)
    try:
        module = importlib.reload(module)
        assert module.engine.dialect.driver == driver
        if "sslmode" in url:
            assert module.engine.url.query["sslmode"] == "require"
        module.engine.dispose()
    finally:
        monkeypatch.setenv("DATABASE_URL", "sqlite://")
        importlib.reload(module)


def test_session_commits_successful_request(db_engine):
    user = User(
        username="committed", email="commit@example.com", hashed_password="hash"
    )
    dependency = get_session()
    session = next(dependency)
    session.add(user)
    user_id = user.id
    with pytest.raises(StopIteration):
        next(dependency)
    with Session(db_engine) as check:
        assert check.get(User, user_id) is not None


def test_session_rolls_back_failed_request(db_engine):
    user = User(
        username="rolledback", email="rollback@example.com", hashed_password="hash"
    )
    dependency = get_session()
    session = next(dependency)
    session.add(user)
    session.flush()
    with pytest.raises(RuntimeError, match="request failed"):
        dependency.throw(RuntimeError("request failed"))
    with Session(db_engine) as check:
        assert check.get(User, user.id) is None
