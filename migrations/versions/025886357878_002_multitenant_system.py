"""Phase 2

Revision ID: 025886357878
Revises: e79f486d661b
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa

revision = '025886357878'
down_revision = 'e79f486d661b'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to tenants table
    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description',     sa.Text(),        nullable=True))
        batch_op.add_column(sa.Column('is_verified',     sa.Boolean(),     nullable=True))
        batch_op.add_column(sa.Column('favicon_url',     sa.String(500),   nullable=True))
        batch_op.add_column(sa.Column('secondary_color', sa.String(10),    nullable=True))
        batch_op.add_column(sa.Column('footer_text',     sa.String(300),   nullable=True))
        batch_op.add_column(sa.Column('custom_css',      sa.Text(),        nullable=True))
        batch_op.add_column(sa.Column('contact_email',   sa.String(200),   nullable=True))
        batch_op.add_column(sa.Column('website_url',     sa.String(300),   nullable=True))
        batch_op.add_column(sa.Column('owner_id',        sa.Integer(),     nullable=True))
        batch_op.add_column(sa.Column('updated_at',      sa.DateTime(),    nullable=True))

    # Add new columns to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bio',             sa.Text(),        nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('bio')

    with op.batch_alter_table('tenants', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('owner_id')
        batch_op.drop_column('website_url')
        batch_op.drop_column('contact_email')
        batch_op.drop_column('custom_css')
        batch_op.drop_column('footer_text')
        batch_op.drop_column('secondary_color')
        batch_op.drop_column('favicon_url')
        batch_op.drop_column('is_verified')
        batch_op.drop_column('description')