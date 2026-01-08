from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import EmailStr


class User(Document):
    """User document model for MongoDB."""
    email: EmailStr
    hashed_password: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"
