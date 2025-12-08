from fastapi import Depends, HTTPException, status
from datetime import datetime, timedelta

from utils.tokens import generate_token, get_hash_token
from schemas.user import User, UserCreate, UserInDB, UserLogin
from database.connection_db import connection
from utils.password import get_password_hash, verify_password
from config.config import settings
import asyncpg


class AuthService:
    async def create_user(
        self,
        user: UserCreate,
        db_pool: asyncpg.Pool = Depends(connection.get_connection),
    ):
        user.email = user.email.lower()

        user.username = user.username.lower()
        plain_password = user.password.get_secret_value()
        hashed_pwd = get_password_hash(plain_password)
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
            RETURNING user_id, email, username, first_name, last_name
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

    async def login_user(
        self,
        user: UserLogin,
        db_pool: asyncpg.Pool = Depends(connection.get_connection),
    ):
        username = user.email or user.username
        fetch_user = "SELECT * FROM users WHERE username = $1 OR email = $1"
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(fetch_user, username)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This user doesn't exist",
            )
        result = dict(result)
        if not verify_password(user.password, result.get("hashed_password")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password",
            )
        if not result.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account is suspended currently",
            )
        if not result.get("is_verified"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account is unverified. Verify your email",
            )
        return result

    async def generate_and_store_tokens(
        self,
        user_id: str,
        db_pool: asyncpg.Pool = Depends(connection.get_connection),
    ):
        user_data = {"user_id": user_id}
        access_token = generate_token(
            user_data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = generate_token(
            user_data,
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            token_type="refresh",
        )
        hashed_refresh = get_hash_token(refresh_token)
        refresh_token_query = """
        INSERT INTO refresh_tokens (user_id, token, expires_at, created_at)
        VALUES ($1, $2, $3, $4)
        """
        expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        async with db_pool.acquire() as conn:
            await conn.fetchrow(
                refresh_token_query, user_id, hashed_refresh, expires_at, datetime.now()
            )
        return {"access_token": access_token, "refresh_token": refresh_token}


auth = AuthService()
