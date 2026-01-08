from datetime import datetime
from typing import List, Optional
from enum import Enum
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    """Order item embedded model."""
    product_id: PydanticObjectId
    name: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class Order(Document):
    """Order document model for MongoDB."""
    user_id: PydanticObjectId
    items: List[OrderItem]
    total: float = Field(gt=0)
    status: OrderStatus = OrderStatus.PENDING
    shipping_address: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "orders"
