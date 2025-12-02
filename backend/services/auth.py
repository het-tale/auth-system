from fastapi import Depends
from datetime import datetime

from schemas.user import UserCreate, UserInDB
from database.connection_db import connection
from utils.password import get_password_hash
import asyncpg


class AuthService:
    async def create_user(
        self,
        user: UserCreate,
        db_pool: asyncpg.Pool = Depends(connection.get_connection)
    ):
        user.email = user.email.lower()

        user.username = user.username.lower()
        hashed_pwd = get_password_hash(str(user.password))
        user_db = UserInDB(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            hash_password=hashed_pwd,
            is_active=True,
            is_verified=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        insert_query = """
            INSERT INTO users (username, email, hashed_password, first_name, last_name, is_verified, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING email, username, first_name, last_name
            """
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(
                insert_query,
                user_db.username,
                user_db.email,
                user_db.hash_password,
                user_db.first_name,
                user_db.last_name,
                user_db.is_verified,
                user_db.is_active,
                user_db.created_at,
                user_db.updated_at,
            )
            return result


auth = AuthService()
