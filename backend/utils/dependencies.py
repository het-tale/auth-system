from typing import Annotated
import asyncpg
from fastapi import Cookie, Depends, HTTPException, status
from jwt import InvalidTokenError, ExpiredSignatureError
from utils.tokens import decode_token
from database.connection_db import connection


def get_access_token(access_token: Annotated[str, Cookie()]):
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return access_token


async def get_current_user(
    token: Annotated[str, Depends(get_access_token)],
    db_pool: asyncpg.Pool = Depends(connection.get_connection),
):
    try:
        payload = decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        get_user_query = "SELECT * FROM users WHERE user_id = $1"
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(get_user_query, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        return user
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    except HTTPException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e),
        )


def get_current_active_user(user=Depends(get_current_user)):
    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive User",
        )
    if not user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email first",
        )
    return user
