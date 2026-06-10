"""Add conversation, message, and memory entry tables.

Revision ID: 004
Revises: 003
Create Date: 2026-06-01 21:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversation table
    op.create_table(
        'conversation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), server_default='New Conversation', nullable=False),
        sa.Column('model', sa.String(), server_default='llama3.2', nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_user_id'), 'conversation', ['user_id'], unique=False)

    # Create message table
    op.create_table(
        'message',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('agent', sa.String(), nullable=True),
        sa.Column('sources', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_message_conversation_id'), 'message', ['conversation_id'], unique=False)

    # Create memory_entry table
    op.create_table(
        'memoryentry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('memory_type', sa.String(), server_default='short_term', nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('ttl', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memoryentry_user_id'), 'memoryentry', ['user_id'], unique=False)
    op.create_index(op.f('ix_memoryentry_memory_type'), 'memoryentry', ['memory_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_memoryentry_memory_type'), table_name='memoryentry')
    op.drop_index(op.f('ix_memoryentry_user_id'), table_name='memoryentry')
    op.drop_table('memoryentry')
    op.drop_index(op.f('ix_message_conversation_id'), table_name='message')
    op.drop_table('message')
    op.drop_index(op.f('ix_conversation_user_id'), table_name='conversation')
    op.drop_table('conversation')
