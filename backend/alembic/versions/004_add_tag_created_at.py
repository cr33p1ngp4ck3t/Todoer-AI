"""Add created_at to tag table

Revision ID: 004_add_tag_created_at
Revises: 003_fix_timezone
Create Date: 2026-01-03 14:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004_add_tag_created_at'
down_revision = '003_fix_timezone'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add created_at column to tag table."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Add created_at column as TIMESTAMPTZ (timezone-aware)
        op.execute("""
            ALTER TABLE tag
            ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)
    else:
        # SQLite fallback
        op.add_column('tag', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()))


def downgrade() -> None:
    """Remove created_at column from tag table."""
    op.drop_column('tag', 'created_at')
