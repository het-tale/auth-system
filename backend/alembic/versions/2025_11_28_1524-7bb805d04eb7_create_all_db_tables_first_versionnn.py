"""create all db tables first versionnn

Revision ID: 7bb805d04eb7
Revises: 
Create Date: 2025-11-28 15:24:04.634578

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7bb805d04eb7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.execute("""
               CREATE TABLE IF NOT EXISTS users (
                   user_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                   email VARCHAR(50) NOT NULL,
                   username VARCHAR(50) NOT NULL,
                   hashed_password VARCHAR(50) NOT NULL,
                   first_name TEXT,
                   last_name TEXT,
                   is_verified BOOLEAN DEFAULT FALSE,
                   is_active BOOLEAN DEFAULT TRUE,
                   two_factor_auth BOOLEAN DEFAULT FALSE,
                   created_at TIMESTAMP,
                   updated_at TIMESTAMP,
                   last_login TIMESTAMP,
                   UNIQUE (email, username)
               );
               """)
    # Create refresh token table
    op.execute("""
               CREATE TABLE IF NOT EXISTS refresh_tokens (
                   refresh_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                   user_id uuid,
                   token TEXT NOT NULL,
                   revoked BOOLEAN DEFAULT FALSE,
                   expires_at TIMESTAMP,
                   created_at TIMESTAMP,
                   CONSTRAINT fk_user_id
                   FOREIGN KEY (user_id)
                   REFERENCES users(user_id)
                   );
               """)
    # Create email verification table
    op.execute("""
               CREATE TABLE IF NOT EXISTS email_verification (
                   email_v_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
                   user_id uuid,
                   token_hash TEXT,
                   expires_at TIMESTAMP,
                   created_at TIMESTAMP,
                   CONSTRAINT fk_user_id
                   FOREIGN KEY (user_id)
                   REFERENCES users(user_id)
               )
               """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
