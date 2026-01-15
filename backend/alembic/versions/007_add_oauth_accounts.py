"""Add OAuth accounts table

Revision ID: 007_add_oauth_accounts
Revises: 006_add_refresh_tokens
Create Date: 2026-01-03 17:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '007_add_oauth_accounts'
down_revision = '006_add_refresh_tokens'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add oauth_account table for social login."""
    op.create_table(
        'oauth_account',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_user_id', sa.String(), nullable=False),
        sa.Column('provider_email', sa.String(), nullable=True),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for performance
    op.create_index('ix_oauth_account_user_id', 'oauth_account', ['user_id'])
    op.create_index('ix_oauth_account_provider', 'oauth_account', ['provider'])
    op.create_index('ix_oauth_account_provider_user_id', 'oauth_account', ['provider_user_id'])

    # Unique constraint: one OAuth account can only be linked to one user
    # (prevents the same Google account from being linked to multiple users)
    op.create_unique_constraint(
        'uq_oauth_provider_user',
        'oauth_account',
        ['provider', 'provider_user_id']
    )


def downgrade() -> None:
    """Remove oauth_account table."""
    op.drop_constraint('uq_oauth_provider_user', 'oauth_account', type_='unique')
    op.drop_index('ix_oauth_account_provider_user_id', 'oauth_account')
    op.drop_index('ix_oauth_account_provider', 'oauth_account')
    op.drop_index('ix_oauth_account_user_id', 'oauth_account')
    op.drop_table('oauth_account')
