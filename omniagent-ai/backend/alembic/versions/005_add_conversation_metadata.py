"""Add conversation metadata columns.

Revision ID: 005
Revises: 004
Create Date: 2026-06-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('conversation', sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('conversation', sa.Column('is_shared', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('conversation', sa.Column('folder_name', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('conversation', 'folder_name')
    op.drop_column('conversation', 'is_shared')
    op.drop_column('conversation', 'is_pinned')
