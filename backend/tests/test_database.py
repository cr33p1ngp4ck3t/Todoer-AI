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
