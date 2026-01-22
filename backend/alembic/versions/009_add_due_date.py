"""Add due_date to task table

Revision ID: 009_add_due_date
Revises: 008_add_chat_tables
Create Date: 2026-01-22 12:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_add_due_date'
down_revision = '008_add_chat_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add due_date column to task table."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Add due_date column as TIMESTAMPTZ (timezone-aware), nullable
        op.execute("""
            ALTER TABLE task
            ADD COLUMN due_date TIMESTAMPTZ NULL
        """)
        # Add index for efficient deadline queries
        op.execute("""
            CREATE INDEX ix_task_due_date ON task (due_date)
        """)
    else:
        # SQLite fallback
        op.add_column('task', sa.Column('due_date', sa.DateTime(), nullable=True))
        op.create_index('ix_task_due_date', 'task', ['due_date'])


def downgrade() -> None:
    """Remove due_date column from task table."""
    op.drop_index('ix_task_due_date', table_name='task')
    op.drop_column('task', 'due_date')
