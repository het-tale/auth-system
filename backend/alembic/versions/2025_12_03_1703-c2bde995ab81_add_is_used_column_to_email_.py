"""add is_used column to email_verification table

Revision ID: c2bde995ab81
Revises: 7f7a6e036575
Create Date: 2025-12-03 17:03:41.867270

"""
from typing import Sequence, Union

from alembic import op



# revision identifiers, used by Alembic.
revision: str = 'c2bde995ab81'
down_revision: Union[str, None] = '7f7a6e036575'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
               ALTER TABLE email_verification
               ADD COLUMN is_used BOOLEAN DEFAULT FALSE
               """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
