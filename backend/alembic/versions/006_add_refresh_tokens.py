"""Add refresh tokens table

Revision ID: 006_add_refresh_tokens
Revises: 005_add_cascade_delete_tags
Create Date: 2026-01-03 16:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_refresh_tokens'
down_revision = '005_add_cascade_delete_tags'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add refresh_token table for JWT token rotation."""
    op.create_table(
        'refresh_token',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('token_hash', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('ix_refresh_token_user_id', 'refresh_token', ['user_id'])
    op.create_index('ix_refresh_token_token_hash', 'refresh_token', ['token_hash'])
    op.create_index('ix_refresh_token_expires_at', 'refresh_token', ['expires_at'])
    op.create_index('ix_refresh_token_revoked', 'refresh_token', ['revoked'])


def downgrade() -> None:
    """Remove refresh_token table."""
    op.drop_index('ix_refresh_token_revoked', 'refresh_token')
    op.drop_index('ix_refresh_token_expires_at', 'refresh_token')
    op.drop_index('ix_refresh_token_token_hash', 'refresh_token')
    op.drop_index('ix_refresh_token_user_id', 'refresh_token')
    op.drop_table('refresh_token')
