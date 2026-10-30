"""Add shared projects, recurring schedules and import deduplication.

Existing task rows remain personal and retain their fields. Reapplying to a
fresh create_all schema is safe. Downgrade removes the new feature data only.
"""

import sqlalchemy as sa
from alembic import op

revision = "010_workspace"
down_revision = "009_add_due_date"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "project" not in tables:
        op.create_table(
            "project",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_project_owner_id", "project", ["owner_id"])
    if "projectmember" not in tables:
        op.create_table(
            "projectmember",
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "project_id", sa.Uuid(), sa.ForeignKey("project.id"), nullable=False
            ),
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("accepted", sa.Boolean(), nullable=False),
            sa.UniqueConstraint("project_id", "user_id", name="uq_project_member"),
        )
        op.create_index("ix_projectmember_project_id", "projectmember", ["project_id"])
        op.create_index("ix_projectmember_user_id", "projectmember", ["user_id"])
    if "taskimport" not in tables:
        op.create_table(
            "taskimport",
            sa.Column("user_id", sa.Uuid(), sa.ForeignKey("user.id"), primary_key=True),
            sa.Column("source_id", sa.Uuid(), primary_key=True),
        )
    columns = {column["name"] for column in sa.inspect(bind).get_columns("task")}
    additions = [
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("assignee_id", sa.Uuid(), nullable=True),
        sa.Column("recurrence", sa.String(), nullable=True),
        sa.Column(
            "recurrence_timezone", sa.String(), nullable=False, server_default="UTC"
        ),
        sa.Column("recurrence_day", sa.Integer(), nullable=True),
        sa.Column(
            "recurrence_spawned",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("predecessor_id", sa.Uuid(), nullable=True),
    ]
    missing = [column for column in additions if column.name not in columns]
    if missing:
        with op.batch_alter_table("task") as batch:
            for column in missing:
                batch.add_column(column)
            if "project_id" not in columns:
                batch.create_foreign_key(
                    "fk_task_project", "project", ["project_id"], ["id"]
                )
                batch.create_index("ix_task_project_id", ["project_id"])
            if "assignee_id" not in columns:
                batch.create_foreign_key(
                    "fk_task_assignee", "user", ["assignee_id"], ["id"]
                )
                batch.create_index("ix_task_assignee_id", ["assignee_id"])
            if "predecessor_id" not in columns:
                batch.create_unique_constraint(
                    "uq_task_predecessor", ["predecessor_id"]
                )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("task")}
    with op.batch_alter_table("task") as batch:
        for foreign_key in sa.inspect(bind).get_foreign_keys("task"):
            if foreign_key["name"] and set(foreign_key["constrained_columns"]) & {
                "project_id",
                "assignee_id",
            }:
                batch.drop_constraint(foreign_key["name"], type_="foreignkey")
        for constraint in sa.inspect(bind).get_unique_constraints("task"):
            if constraint["name"] and constraint["column_names"] == ["predecessor_id"]:
                batch.drop_constraint(constraint["name"], type_="unique")
        for index in sa.inspect(bind).get_indexes("task"):
            if set(index["column_names"]) & {
                "project_id",
                "assignee_id",
                "predecessor_id",
            }:
                batch.drop_index(index["name"])
        for name in (
            "project_id",
            "assignee_id",
            "recurrence",
            "recurrence_timezone",
            "recurrence_day",
            "recurrence_spawned",
            "predecessor_id",
        ):
            if name in columns:
                batch.drop_column(name)
    for table in ("taskimport", "projectmember", "project"):
        if table in sa.inspect(bind).get_table_names():
            op.drop_table(table)
