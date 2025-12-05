from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse


from schemas.email import VerificationEmail
from schemas.user import User, UserCreate, UserLogin
from database.connection_db import connection
import asyncpg
from services.auth import auth
from services.email_verification import email_verification
from test import get_hash_token
from utils.tokens import generate_token
from config.config import settings


auth_route = APIRouter(tags=["Authentication"])


@auth_route.post("/register", response_model=User)
async def register(
    user: UserCreate,
    background_task: BackgroundTasks,
    db_pool: asyncpg.Pool = Depends(connection.get_connection),
):
    if user.confirm_password != user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and Confirm Password don't macth ",
        )
    query = "SELECT email, username FROM users WHERE email = $1 OR username = $2"
    async with db_pool.acquire() as conn:
        result = await conn.fetch(query, user.email.lower(), user.username.lower())
    if result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The provided email or username already exists",
        )
    result = await auth.create_user(user, db_pool)
    if result:
        user_out = dict(result)
        email_verif_token = await email_verification.generate_and_save_token(
            str(user_out.get("user_id", 0)), db_pool
        )
        email_data = VerificationEmail(
            email=[user_out.get("email")],
            body={
                "receiver": user_out.get("username"),
                "app_name": "Touch Somebody",
                "verification_link": f"http://localhost:8000/verify_email?token={email_verif_token}",
            },
        )
        await email_verification.send_email(email_data, background_task)
        return User(**user_out)
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to Register user",
        )


@auth_route.get("/verify_email")
async def verify_email(
    token: Annotated[str, Query()],
    db_pool: asyncpg.Pool = Depends(connection.get_connection),
):
    result = await email_verification.verify_email_token(token, db_pool)
    return {"Result": result}


@auth_route.post("/login", response_model=User)
async def authenticate_user(
    user: UserLogin,
    db_pool: asyncpg.Pool = Depends(connection.get_connection),
):
    if user.email and user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either username or email not both",
        )
    try:
        logged_user = await auth.login_user(user, db_pool)
        user_id = str(logged_user.get("user_id"))
        tokens = await auth.generate_and_store_tokens(user, user_id, db_pool)
        res = JSONResponse(
            content={
                "user_id": user_id,
                "email": logged_user.get("email"),
                "username": logged_user.get("username"),
                "first_name": logged_user.get("first_name"),
                "last_name": logged_user.get("last_name"),
                "access_token": tokens.get("access_token"),
            }
        )
        res.set_cookie(
            key="access_token",
            value=tokens.get("access_token"),
            httponly=True,
            samesite="Lax",
            secure=True,
            max_age=15*60,
            path="/",
        )
        res.set_cookie(
            key="refresh_token",
            value=tokens.get("refresh_token"),
            httponly=True,
            samesite="Lax",
            secure=True,
            max_age=7*24*60*60,
            path="/",
        )
        return res
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@auth_route.post("/refresh")
async def regenrate_access_token(
    refresh_token: Annotated[str, Cookie()],
    db_pool: asyncpg.Pool = Depends(connection.get_connection)):
    hashed_token = get_hash_token(refresh_token)
    refresh_query = "SELECT * FROM refresh_tokens WHERE token = $1"
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(refresh_query, hashed_token)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    result = dict(result)
    expire_date = result.get("expires_at")
    if expire_date < datetime.now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    query_user = "SELECT * FROM users WHERE user_id = $1"
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(query_user, result.get("user_id"))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User Not Found")
    user_data = dict(user)
    if not user_data.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='This user is not active')
    if result.get("revoked"):
        user_associated_tokens = "UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = $1"
        async with db_pool.acquire() as conn:
            await conn.fetch(user_associated_tokens, user_data.get("user_id"))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access")
    # implements rotation
    user_associated_token = "UPDATE refresh_tokens SET revoked = TRUE WHERE refresh_id = $1"
    async with db_pool.acquire() as conn:
            await conn.fetch(user_associated_token, result.get("refresh_id"))
    tokens = await auth.generate_and_store_tokens(User(**user_data), user_data.get("user_id"), db_pool)
    res = JSONResponse(
            content={
                "user_id": user_data.get("user_id"),
                "email": user_data.get("email"),
                "username": user_data.get("username"),
                "first_name": user_data.get("first_name"),
                "last_name": user_data.get("last_name"),
                "access_token": tokens.get("access_token"),
            }
        )
    res.set_cookie(
            key="access_token",
            value=tokens.get("access_token"),
            httponly=True,
            samesite="Lax",
            secure=True,
            max_age=15*60,
            path="/",
        )
    res.set_cookie(
            key="refresh_token",
            value=tokens.get("refresh_token"),
            httponly=True,
            samesite="Lax",
            secure=True,
            max_age=7*24*60*60,
            path="/",
        )
    return res