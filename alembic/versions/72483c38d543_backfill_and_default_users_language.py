"""backfill and default users.language

Revision ID: 72483c38d543
Revises: 86bb42e9ea4b
Create Date: 2026-07-07 02:22:21.077915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '72483c38d543'
down_revision: Union[str, Sequence[str], None] = '86bb42e9ea4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("UPDATE users SET language = 'en' WHERE language IS NULL")
    op.alter_column('users', 'language', server_default='en', nullable=False)

def downgrade():
    op.alter_column('users', 'language', server_default=None, nullable=True)
