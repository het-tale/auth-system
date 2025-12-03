from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator
import re


class UserLogin(BaseModel):
    username: Optional[str] = Field(
        min_length=4, max_length=20, pattern=r"^[a-zA-Z0-9]+$", default=None
    )
    email: EmailStr | None = None
    password: str


class User(BaseModel):
    username: str = Field(min_length=4, max_length=20, pattern=r"^[a-zA-Z0-9]+$")
    first_name: str = Field(min_length=2)
    last_name: str = Field(min_length=2)
    email: EmailStr


class UserCreate(User):
    password: SecretStr
    confirm_password: SecretStr

    @field_validator("password", "confirm_password")
    @classmethod
    def validate_password(cls, value: SecretStr):
        password_value = value.get_secret_value()
        if len(password_value) < 8:
            raise ValueError("Password must contain at least 8 characters")
        pattern = re.compile(
            '^(?=(.*[a-z]){2,})(?=.*[A-Z])(?=.*\d)(?=.*[@#$%^&+=!"])([a-zA-Z\d@#$%^&+=!]+)$'
        )
        if not re.search(pattern, password_value):
            raise ValueError(
                "The password must contain at least one capital letter, one digit and one special character"
            )
        return value


class UserInDB(User):
    hash_password: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
