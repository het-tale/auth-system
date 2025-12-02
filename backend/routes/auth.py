from fastapi import APIRouter, Depends, HTTPException, status

from schemas.user import User, UserCreate
from database.connection_db import connection
import asyncpg
from services.auth import auth


auth_route = APIRouter(tags=["Authentication"])


@auth_route.post("/register", response_model=User)
async def register(
    user: UserCreate,
    db_pool: asyncpg.Pool = Depends(connection.get_connection)
):
    if user.confirm_password != user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password and Confirm Password don't macth ",
        )
    query = "SELECT email, username FROM users WHERE email = $1 OR username = $2"
    async with db_pool.acquire() as conn:
        result = await conn.fetch(
            query, user.email.lower(), user.username.lower())
    if result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The provided email or username already exists",
        )
    result = await auth.create_user(user, db_pool)
    if result:
        return User(**dict(result))
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to Register user",
        )
