from datetime import datetime
from pydantic import BaseModel


class Email(BaseModel):
    user_id: str
    token_hash: str
    created_at: datetime
    expires_at: datetime
