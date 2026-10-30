"""New schema migration must retain legacy user/task/tag data and be reversible."""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_workspace_migration_preserves_legacy_rows_and_round_trips():
    path = Path(__file__).parents[1] / "alembic/versions/010_workspace.py"
    spec = importlib.util.spec_from_file_location("workspace_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE user (id CHAR(32) PRIMARY KEY, email TEXT)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE task (id CHAR(32) PRIMARY KEY, owner_id CHAR(32), title TEXT, due_date DATETIME)"
        )
        connection.exec_driver_sql(
            "CREATE TABLE tag (id CHAR(32) PRIMARY KEY, task_id CHAR(32), name TEXT)"
        )
        connection.exec_driver_sql(
            "INSERT INTO user VALUES ('owner', 'owner@example.com')"
        )
        connection.exec_driver_sql(
            "INSERT INTO task VALUES ('task', 'owner', 'Preserve me', NULL)"
        )
        connection.exec_driver_sql("INSERT INTO tag VALUES ('tag', 'task', 'work')")
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            migration.upgrade()
            columns = {
                column["name"] for column in sa.inspect(connection).get_columns("task")
            }
            assert {
                "project_id",
                "recurrence",
                "assignee_id",
                "recurrence_spawned",
            } <= columns
            assert connection.exec_driver_sql(
                "SELECT title, recurrence_timezone, recurrence_spawned FROM task"
            ).one() == ("Preserve me", "UTC", 0)
            assert {"project", "projectmember", "taskimport"} <= set(
                sa.inspect(connection).get_table_names()
            )
            migration.upgrade()
            migration.downgrade()
        assert (
            connection.exec_driver_sql("SELECT title FROM task").scalar_one()
            == "Preserve me"
        )
        assert connection.exec_driver_sql("SELECT name FROM tag").scalar_one() == "work"
        assert (
            connection.exec_driver_sql("SELECT email FROM user").scalar_one()
            == "owner@example.com"
        )
        assert "recurrence" not in {
            column["name"] for column in sa.inspect(connection).get_columns("task")
        }
    engine.dispose()
