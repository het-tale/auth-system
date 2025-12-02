"""update the hashed password type to TEXT

Revision ID: 88cdaa545571
Revises: 7bb805d04eb7
Create Date: 2025-12-02 18:14:37.016813

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '88cdaa545571'
down_revision: Union[str, None] = '7bb805d04eb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # alter users table
    op.execute("""
               ALTER TABLE users
               ALTER COLUMN hashed_password TYPE TEXT NOT NULL
               """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE users")
    op.execute("DROP TABLE refresh_tokens")
    op.execute("DROP TABLE email_verification")
