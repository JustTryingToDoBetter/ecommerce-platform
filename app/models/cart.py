from datetime import datetime
from typing import List
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    """Cart item embedded model."""
    product_id: PydanticObjectId
    quantity: int = Field(gt=0, default=1)
    price: float = Field(gt=0)


class Cart(Document):
    """Cart document model for MongoDB."""
    user_id: PydanticObjectId
    items: List[CartItem] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "carts"
