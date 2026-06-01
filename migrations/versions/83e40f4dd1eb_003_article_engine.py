"""Phase 3 - articles

Revision ID: 83e40f4dd1eb
Revises: 025886357878
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa

revision = '83e40f4dd1eb'
down_revision = '025886357878'
branch_labels = None
depends_on = None


def upgrade():
    # Table already exists — just stamp it as applied
    pass


def downgrade():
    pass