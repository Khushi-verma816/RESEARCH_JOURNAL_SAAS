"""Add transactions table

Revision ID: 9b5052c8c9f5
Revises: 2649ecb19f8b
Create Date: 2026-03-26 11:22:40.848221
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9b5052c8c9f5'
down_revision = '2649ecb19f8b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('subscription_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.String(length=200), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('approved_by_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['subscription_id'], ['subscriptions.id'], ),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True          
    )


def downgrade():
    op.drop_table('transactions')