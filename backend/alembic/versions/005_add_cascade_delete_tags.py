"""Add CASCADE delete to tag.task_id foreign key

Revision ID: 005_add_cascade_delete_tags
Revises: 004_add_tag_created_at
Create Date: 2026-01-03 15:00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '005_add_cascade_delete_tags'
down_revision = '004_add_tag_created_at'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add CASCADE delete to tag foreign key."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Drop existing foreign key constraint
        op.execute("""
            ALTER TABLE tag
            DROP CONSTRAINT IF EXISTS tag_task_id_fkey
        """)

        # Add foreign key with CASCADE delete
        op.execute("""
            ALTER TABLE tag
            ADD CONSTRAINT tag_task_id_fkey
            FOREIGN KEY (task_id) REFERENCES task(id) ON DELETE CASCADE
        """)


def downgrade() -> None:
    """Remove CASCADE delete from tag foreign key."""
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # Drop CASCADE foreign key
        op.execute("""
            ALTER TABLE tag
            DROP CONSTRAINT IF EXISTS tag_task_id_fkey
        """)

        # Add foreign key without CASCADE
        op.execute("""
            ALTER TABLE tag
            ADD CONSTRAINT tag_task_id_fkey
            FOREIGN KEY (task_id) REFERENCES task(id)
        """)
