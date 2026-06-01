"""Phase 4 billing

Revision ID: 2649ecb19f8b
Revises: 83e40f4dd1eb
Create Date: 2026-03-05 19:28:49.881827

"""
from alembic import op
import sqlalchemy as sa

revision = '2649ecb19f8b'
down_revision = '83e40f4dd1eb'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('subscriptions',
        sa.Column('id',                     sa.Integer(),     nullable=False),
        sa.Column('tenant_id',              sa.Integer(),     nullable=False),
        sa.Column('plan',                   sa.String(50),    nullable=True),
        sa.Column('status',                 sa.String(50),    nullable=True),
        sa.Column('amount',                 sa.Float(),       nullable=True),
        sa.Column('currency',               sa.String(10),    nullable=True),
        sa.Column('billing_cycle',          sa.String(20),    nullable=True),
        sa.Column('started_at',             sa.DateTime(),    nullable=True),
        sa.Column('expires_at',             sa.DateTime(),    nullable=True),
        sa.Column('cancelled_at',           sa.DateTime(),    nullable=True),
        sa.Column('trial_ends_at',          sa.DateTime(),    nullable=True),
        sa.Column('stripe_customer_id',     sa.String(200),   nullable=True),
        sa.Column('stripe_subscription_id', sa.String(200),   nullable=True),
        sa.Column('created_at',             sa.DateTime(),    nullable=True),
        sa.Column('updated_at',             sa.DateTime(),    nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_sub_tenant'),
        sa.PrimaryKeyConstraint('id', name='pk_subscriptions')
    )


def downgrade():
    op.drop_table('subscriptions')