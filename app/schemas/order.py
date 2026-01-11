
from pydantic import BaseModel, Field
from typing import List, Optional 
from beanie import PydanticObjectId
from datetime import datetime
from app.models.order import OrderStatus

# Schema for creating order items
class OrderItemCreate(BaseModel):
    product_id: PydanticObjectId
    quantity: int = Field(gt=0)
## OrderCreate
# Schema for creating an order
class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    shipping_address: str

## OrdertimeResponse

class OrderItemResponse(BaseModel):
    ## single order itme with product details
    product_id : PydanticObjectId
    name: str
    description: str
    price : float
## OrderResponse
class OrderResponse(BaseModel):
    id : PydanticObjectId
    user_id : PydanticObjectId
    items: List[OrderItemResponse]
    status : OrderStatus
    total : float
    shipping_address : Optional[str]
    created_at : datetime
    updated_at : datetime

    class Config:
        from_attributes = True


## OrderList
class OrderList(BaseModel):
    orders : List[OrderResponse]
    total : int
    page: int
    size : int