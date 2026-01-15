"""Add username to user table

Revision ID: 002_add_username
Revises: 001_initial
Create Date: 2026-01-02 10:15:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_username'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add username column (nullable first for existing data)
    op.add_column('user', sa.Column('username', sa.String(), nullable=True))

    # Update existing users to have a username based on their email
    # Use SQL standard substring function for Neon PostgreSQL compatibility
    op.execute("""
        UPDATE "user"
        SET username = SUBSTRING(email FROM 1 FOR POSITION('@' IN email) - 1)
        WHERE username IS NULL
    """)

    # Make username non-nullable and add constraints
    op.alter_column('user', 'username', nullable=False)
    op.create_unique_constraint('uq_user_username', 'user', ['username'])
    op.create_index('ix_user_username', 'user', ['username'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_user_username', 'user')
    op.drop_constraint('uq_user_username', 'user', type_='unique')
    op.drop_column('user', 'username')
