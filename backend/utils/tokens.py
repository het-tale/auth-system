from datetime import timedelta, datetime, timezone
import secrets

from fastapi import HTTPException, status
import jwt
from config.config import settings
import uuid
import hashlib


def generate_token(
    data: dict,
    expiry_date: timedelta | None = None,
    token_type: str = "access"
):
    payload = data.copy()
    if expiry_date:
        expire = datetime.now(tz=timezone.utc) + expiry_date
    else:
        expire = (
            datetime.now(tz=timezone.utc)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            if token_type == "access"
            else datetime.now(tz=timezone.utc)
            + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
    issued_at = datetime.now(tz=timezone.utc)
    if token_type == "access":
        payload.update({"exp": expire, "iat": issued_at})
    else:
        payload.update(
            {"exp": expire, "iat": issued_at, "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(
        payload, settings.TOKEN_SECRET_KEY, settings.TOKEN_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.TOKEN_SECRET_KEY,
            settings.TOKEN_ALGORITHM)
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def get_hash_token(token: str):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_verification_token():
    return secrets.token_urlsafe(32)
