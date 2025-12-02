"""update the hashed password type to TEXTT

Revision ID: 7f7a6e036575
Revises: 88cdaa545571
Create Date: 2025-12-02 18:30:27.891712

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7f7a6e036575'
down_revision: Union[str, None] = '88cdaa545571'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
               ALTER TABLE users
               ALTER COLUMN hashed_password TYPE TEXT
               """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
