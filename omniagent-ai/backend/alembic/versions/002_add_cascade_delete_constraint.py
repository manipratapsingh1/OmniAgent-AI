"""Add CASCADE DELETE constraint to documentchunk foreign key.

Revision ID: 002
Revises: 001
Create Date: 2026-05-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add CASCADE DELETE to documentchunk.document_id foreign key"""
    # Drop the old foreign key constraint
    op.drop_constraint('documentchunk_document_id_fkey', 'documentchunk', type_='foreignkey')
    
    # Add new foreign key with CASCADE DELETE
    op.create_foreign_key(
        'documentchunk_document_id_fkey',
        'documentchunk',
        'document',
        ['document_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove CASCADE DELETE and revert to standard foreign key"""
    # Drop the CASCADE foreign key
    op.drop_constraint('documentchunk_document_id_fkey', 'documentchunk', type_='foreignkey')
    
    # Add back the original foreign key without CASCADE
    op.create_foreign_key(
        'documentchunk_document_id_fkey',
        'documentchunk',
        'document',
        ['document_id'],
        ['id']
    )
