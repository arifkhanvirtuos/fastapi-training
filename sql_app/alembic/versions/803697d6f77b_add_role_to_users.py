"""add_role_to_users

Revision ID: 803697d6f77b
Revises: ccb59ee5e5a6
Create Date: 2026-02-02 10:46:05.427371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '803697d6f77b'
down_revision: Union[str, None] = 'ccb59ee5e5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM type for user roles explicitly
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'manager', 'user', 'guest')")
    
    # Add role column to users table with default 'user'
    op.add_column('users', sa.Column('role', sa.Enum('admin', 'manager', 'user', 'guest', name='userrole', create_type=False), nullable=False, server_default='user'))


def downgrade() -> None:
    # Remove role column
    op.drop_column('users', 'role')
    
    # Drop the ENUM type
    op.execute("DROP TYPE IF EXISTS userrole")
