"""Add new fields to Document model for better error tracking and chunk management.

Revision ID: 001
Revises: 
Create Date: 2026-05-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new columns to document table"""
    # Add new columns with defaults for existing rows
    op.add_column('document', sa.Column('embedding_status', sa.String(), server_default='pending', nullable=False))
    op.add_column('document', sa.Column('chunk_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('document', sa.Column('error_message', sa.String(length=500), nullable=True))
    op.add_column('document', sa.Column('last_indexed_at', sa.DateTime(), nullable=True))
    op.add_column('document', sa.Column('vector_ids_prefix', sa.String(), server_default='', nullable=False))
    op.add_column('document', sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False))
    
    # Update vector_id column in document_chunk to be required
    op.alter_column('documentchunk', 'vector_id', existing_type=sa.String(), nullable=False, server_default='')


def downgrade() -> None:
    """Remove new columns from document table"""
    op.drop_column('document', 'updated_at')
    op.drop_column('document', 'vector_ids_prefix')
    op.drop_column('document', 'last_indexed_at')
    op.drop_column('document', 'error_message')
    op.drop_column('document', 'chunk_count')
    op.drop_column('document', 'embedding_status')
    
    # Revert vector_id to optional
    op.alter_column('documentchunk', 'vector_id', existing_type=sa.String(), nullable=True, server_default=None)
