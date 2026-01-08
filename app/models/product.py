from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import Field


class Product(Document):
    """Product document model for MongoDB."""
    name: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    category: Optional[str] = None
    tags: List[str] = []
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "products"
