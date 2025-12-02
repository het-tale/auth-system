from datetime import datetime, timedelta, timezone
import asyncpg
from fastapi import Depends
from database.connection_db import connection
from utils.tokens import generate_verification_token, get_hash_token
from config.config import settings


class EmailVerification:
    async def generate_and_save_token(
        self, user_id: str, db_pool: asyncpg.Pool = Depends(connection.get_connection)
    ):
        token = generate_verification_token()
        hashed_token = get_hash_token(token)
        expires_at = datetime.now() + timedelta(
            hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS
        )
        query = """
        INSERT INTO email_verification (user_id, token_hash, expires_at, created_at)
        VALUES ($1, $2, $3, $4)
        """
        async with db_pool.acquire() as conn:
            await conn.fetchrow(
                query, user_id, hashed_token, expires_at, datetime.now()
            )
        return token


email_verification = EmailVerification()
