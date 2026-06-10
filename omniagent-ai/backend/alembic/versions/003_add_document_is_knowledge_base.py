"""Add is_knowledge_base field to document table.

Revision ID: 003
Revises: 002
Create Date: 2026-06-01 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'document',
        sa.Column('is_knowledge_base', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('document', 'is_knowledge_base')
