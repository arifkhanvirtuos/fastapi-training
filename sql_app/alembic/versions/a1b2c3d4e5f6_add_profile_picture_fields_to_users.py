"""add_profile_picture_fields_to_users

Revision ID: a1b2c3d4e5f6
Revises: 803697d6f77b
Create Date: 2026-02-06 10:53:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '803697d6f77b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add profile picture URL columns to users table
    op.add_column('users', sa.Column('profile_picture_url', sa.String(length=500), nullable=True))
    op.add_column('users', sa.Column('profile_picture_thumbnail_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    # Remove profile picture URL columns
    op.drop_column('users', 'profile_picture_thumbnail_url')
    op.drop_column('users', 'profile_picture_url')
