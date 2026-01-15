"""Add conversation and message tables for AI chatbot

Revision ID: 008_add_chat_tables
Revises: 007_add_oauth_accounts
Create Date: 2026-01-03 18:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_add_chat_tables'
down_revision = '007_add_oauth_accounts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add conversation and message tables for chat feature."""

    # Create conversation table
    op.create_table(
        'conversation',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for conversation
    op.create_index('ix_conversation_user_id', 'conversation', ['user_id'])
    op.create_index('ix_conversation_created_at', 'conversation', ['created_at'])

    # Create message table
    op.create_table(
        'message',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_calls', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for message
    op.create_index('ix_message_conversation_id', 'message', ['conversation_id'])
    op.create_index('ix_message_role', 'message', ['role'])
    op.create_index('ix_message_created_at', 'message', ['created_at'])


def downgrade() -> None:
    """Remove conversation and message tables."""

    # Drop message table and its indexes
    op.drop_index('ix_message_created_at', 'message')
    op.drop_index('ix_message_role', 'message')
    op.drop_index('ix_message_conversation_id', 'message')
    op.drop_table('message')

    # Drop conversation table and its indexes
    op.drop_index('ix_conversation_created_at', 'conversation')
    op.drop_index('ix_conversation_user_id', 'conversation')
    op.drop_table('conversation')
