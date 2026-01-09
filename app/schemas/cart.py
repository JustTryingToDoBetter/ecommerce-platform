

## cart schema.py
from beanie import PydanticObjectId
from pydantic import BaseModel
from typing import List
class CartItemAdd(BaseModel):
    product_id: PydanticObjectId
    quantity: int

class CartItemUpdate(BaseModel):
    product_id: PydanticObjectId
    quantity: int

class CartItemResponse(BaseModel):
    product_id: PydanticObjectId
    quantity: int
    price: float

class CartResponse(BaseModel):
    items: List[CartItemResponse] ## List of items in the cart
    total_price: float