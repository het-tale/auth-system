from datetime import datetime, timedelta
from pathlib import Path
import asyncpg
from fastapi import BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from schemas.email import VerificationEmail
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
        self, user_id: str,
        db_pool: asyncpg.Pool = Depends(connection.get_connection)
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
        background_tasks.add_task(
            fm.send_message, message, template_name="verify.html")
        return JSONResponse(
            status_code=200, content={"message": "email has been sent"})


email_verification = EmailVerification()
