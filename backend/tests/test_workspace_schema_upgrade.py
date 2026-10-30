"""Unversioned local databases get only the additive workspace transition."""

from importlib import import_module

import pytest
from sqlalchemy import create_engine, inspect, text


def test_local_schema_upgrade_preserves_data_and_repeats(tmp_path):
    upgrade = import_module("src.lib.migrate_workspace").upgrade_workspace
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE user (id CHAR(32) PRIMARY KEY, username TEXT, email TEXT, hashed_password TEXT, is_active BOOLEAN, created_at DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE task (id CHAR(32) PRIMARY KEY, owner_id CHAR(32), title TEXT, description TEXT, status TEXT, priority TEXT, due_date DATETIME, created_at DATETIME, updated_at DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE tag (id CHAR(32) PRIMARY KEY, task_id CHAR(32), name TEXT, created_at DATETIME)"
        )
        connection.exec_driver_sql(
            "INSERT INTO task (id,title,status,priority) VALUES ('legacy','Keep this','pending','medium')"
        )
    upgrade(engine)
    upgrade(engine)
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT title, recurrence_timezone FROM task")
        ).one() == ("Keep this", "UTC")
        assert "alembic_version" not in inspect(connection).get_table_names()
    engine.dispose()


def test_local_schema_upgrade_rejects_unknown_or_versioned_schema(tmp_path):
    upgrade = import_module("src.lib.migrate_workspace").upgrade_workspace
    engine = create_engine(f"sqlite:///{tmp_path / 'unknown.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE task (id TEXT PRIMARY KEY, title TEXT)"
        )
    with pytest.raises(ValueError, match="legacy schema"):
        upgrade(engine)
    assert inspect(engine).get_table_names() == ["task"]
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE alembic_version (version_num TEXT)")
    with pytest.raises(ValueError, match="Alembic"):
        upgrade(engine)
    engine.dispose()


def test_local_schema_upgrade_rolls_back_ddl_on_failure(tmp_path, monkeypatch):
    module = import_module("src.lib.migrate_workspace")
    engine = create_engine(f"sqlite:///{tmp_path / 'rollback.db'}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE user (id CHAR(32) PRIMARY KEY, username TEXT, email TEXT, hashed_password TEXT, is_active BOOLEAN, created_at DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE task (id CHAR(32) PRIMARY KEY, owner_id CHAR(32), title TEXT, description TEXT, status TEXT, priority TEXT, due_date DATETIME, created_at DATETIME, updated_at DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE tag (id CHAR(32) PRIMARY KEY, task_id CHAR(32), name TEXT, created_at DATETIME)"
        )
    original = module.Operations.create_table

    def fail_after_one_table(self, table_name, *args, **kwargs):
        if table_name == "projectmember":
            raise RuntimeError("Interrupted migration")
        return original(self, table_name, *args, **kwargs)

    monkeypatch.setattr(module.Operations, "create_table", fail_after_one_table)
    with pytest.raises(RuntimeError, match="Interrupted migration"):
        module.upgrade_workspace(engine)
    assert set(inspect(engine).get_table_names()) == {"user", "task", "tag"}
    engine.dispose()
