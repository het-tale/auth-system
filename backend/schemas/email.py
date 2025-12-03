from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr


class Email(BaseModel):
    user_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime


class VerificationEmail(BaseModel):
    email: list[EmailStr]
    body: dict[str, Any]
