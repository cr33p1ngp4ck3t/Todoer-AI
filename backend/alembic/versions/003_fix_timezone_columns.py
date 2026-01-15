"""Fix timezone-aware datetime columns

Revision ID: 003_fix_timezone
Revises: 002_add_username
Create Date: 2026-01-02 12:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_fix_timezone'
down_revision = '002_add_username'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert datetime columns to timezone-aware TIMESTAMPTZ."""
    # Check if using PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # User table
        op.execute("""
            ALTER TABLE "user"
            ALTER COLUMN created_at TYPE TIMESTAMPTZ
            USING created_at AT TIME ZONE 'UTC'
        """)

        # Task table
        op.execute("""
            ALTER TABLE task
            ALTER COLUMN created_at TYPE TIMESTAMPTZ
            USING created_at AT TIME ZONE 'UTC',
            ALTER COLUMN updated_at TYPE TIMESTAMPTZ
            USING updated_at AT TIME ZONE 'UTC'
        """)

        # Note: tag table doesn't have created_at column in initial migration


def downgrade() -> None:
    """Revert to timezone-naive TIMESTAMP."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('ALTER TABLE "user" ALTER COLUMN created_at TYPE TIMESTAMP')
        op.execute('ALTER TABLE task ALTER COLUMN created_at TYPE TIMESTAMP, ALTER COLUMN updated_at TYPE TIMESTAMP')
