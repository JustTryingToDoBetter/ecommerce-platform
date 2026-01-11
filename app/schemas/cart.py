

## cart schema.py
from beanie import PydanticObjectId
from pydantic import BaseModel, Field
from typing import List

class CartItemAdd(BaseModel):
    product_id: PydanticObjectId
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")

class CartItemUpdate(BaseModel):
    product_id: PydanticObjectId
    quantity: int = Field(..., gt=0, description="Quantity must be greater than 0")

class CartItemResponse(BaseModel):
    product_id: PydanticObjectId
    quantity: int
    price: float

class CartResponse(BaseModel):
    items: List[CartItemResponse] ## List of items in the cart
    total_price: float