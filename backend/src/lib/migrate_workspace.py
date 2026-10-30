"""Apply the additive workspace migration to an unversioned create_all database."""

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect


def upgrade_workspace(engine):
    legacy_columns = {
        "user": {
            "id",
            "username",
            "email",
            "hashed_password",
            "is_active",
            "created_at",
        },
        "task": {
            "id",
            "owner_id",
            "title",
            "description",
            "status",
            "priority",
            "due_date",
            "created_at",
            "updated_at",
        },
        "tag": {"id", "task_id", "name", "created_at"},
    }
    workspace_columns = {
        "project_id",
        "assignee_id",
        "recurrence",
        "recurrence_timezone",
        "recurrence_day",
        "recurrence_spawned",
        "predecessor_id",
    }
    path = (
        Path(__file__).resolve().parents[2]
        / "alembic"
        / "versions"
        / "010_workspace.py"
    )
    spec = importlib.util.spec_from_file_location("workspace_transition", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with engine.begin() as connection:
        # SQLite needs an explicit transaction before DDL to make rollback atomic.
        if connection.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN")
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())
        if "alembic_version" in tables:
            raise ValueError("Use Alembic upgrade head for a versioned database")
        for table, required in legacy_columns.items():
            if table not in tables or not required <= {
                column["name"] for column in inspector.get_columns(table)
            }:
                raise ValueError(
                    "Unrecognized legacy schema; review migrations before changing this database"
                )
        present = workspace_columns & {
            column["name"] for column in inspector.get_columns("task")
        }
        if present and present != workspace_columns:
            raise ValueError(
                "Partial workspace schema; review before applying the migration"
            )
        expected_tables = {
            "project": {"id", "name", "owner_id", "created_at"},
            "projectmember": {"id", "project_id", "user_id", "role", "accepted"},
            "taskimport": {"user_id", "source_id"},
        }
        existing_tables = set(expected_tables) & tables
        if existing_tables and (
            existing_tables != set(expected_tables) or present != workspace_columns
        ):
            raise ValueError(
                "Partial workspace schema; review before applying the migration"
            )
        for table in existing_tables:
            if not expected_tables[table] <= {
                column["name"] for column in inspector.get_columns(table)
            }:
                raise ValueError(
                    "Unrecognized workspace schema; review before applying the migration"
                )
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            migration.upgrade()


if __name__ == "__main__":
    from src.lib.database import engine

    upgrade_workspace(engine)
    print("Workspace schema upgraded; existing data preserved.")
