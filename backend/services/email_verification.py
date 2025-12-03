from datetime import datetime, timedelta
from pathlib import Path
import asyncpg
from fastapi import BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from schemas.email import Email, VerificationEmail
from database.connection_db import connection
from utils.tokens import generate_verification_token, get_hash_token
from config.config import settings
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType


class EmailVerification:
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.MAIL_USERNAME,
        MAIL_PASSWORD=settings.MAIL_PASSWORD,
        MAIL_PORT=settings.MAIL_PORT,
        MAIL_FROM=settings.MAIL_FROM,
        MAIL_SERVER=settings.MAIL_SERVER,
        MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=settings.USE_CREDENTIALS,
        TEMPLATE_FOLDER=Path(__file__).parent / ".." / "templates",
    )

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

    async def send_email(
        self,
        email: VerificationEmail,
        background_tasks: BackgroundTasks,
    ):
        message = MessageSchema(
            subject="Touch Somebody Email Verification",
            recipients=email.model_dump().get("email"),
            template_body=email.model_dump().get("body"),
            subtype=MessageType.html,
        )
        fm = FastMail(self.conf)
        background_tasks.add_task(fm.send_message, message, template_name="verify.html")
        return JSONResponse(status_code=200, content={"message": "email has been sent"})

    async def verify_email_token(
        self, token: str, db_pool: asyncpg.Pool = Depends(connection.get_connection)
    ):
        hashed_token = get_hash_token(token)
        email_query = "SELECT * FROM email_verification WHERE token_hash = $1"
        async with db_pool.acquire() as conn:
            result = await conn.fetchrow(email_query, hashed_token)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid Verification token",
            )
        result = dict(result)
        email_verification_row = Email(
            user_id=str(result.get("user_id")),
            token_hash=result.get("token_hash"),
            is_used=result.get("is_used"),
            expires_at=result.get("expires_at"),
            created_at=result.get("created_at"),
        )
        print(email_verification_row)
        expires_at = result.get("expires_at")
        if datetime.now() > expires_at:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The token has been expired. Please request a new one",
            )
        if result.get("is_used"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This token has been used. if you believe your account still deactivated please request a new one",
            )
        user_verified_query = "UPDATE users SET is_verified = TRUE WHERE user_id = $1"
        async with db_pool.acquire() as conn:
            await conn.fetchrow(user_verified_query, result.get("user_id"))
        update_email_row = "UPDATE email_verification SET is_used = TRUE WHERE email_v_id = $1"
        async with db_pool.acquire() as conn:
            await conn.fetchrow(update_email_row, result.get("email_v_id"))
        return email_verification_row.model_dump()


email_verification = EmailVerification()
