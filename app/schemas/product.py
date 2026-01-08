## request/ response schemas for product operations

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProductCreate(BaseModel):
    name:str = Field(..., min_length=1, max_length=100, description="Name of the product")
    description:Optional[str] = Field(None, max_length=500, description="Description of the product")
    price:float = Field(..., gt=0, description="Price of the product")
    stock:int = Field(0, ge=0, description="Available stock of the product")
    category:Optional[str] = Field(None, max_length=50, description="Category of the product")
    tags:Optional[list[str]] = Field([], description="Tags associated with the product")



class ProductUpdate(BaseModel):
    name:Optional[str] = Field(None, min_length=1, max_length=100, description="Name of the product")
    description:Optional[str] = Field(None, max_length=500, description="Description of the product")
    price:Optional[float] = Field(None, gt=0, description="Price of the product")
    stock:Optional[int] = Field(None, ge=0, description="Available stock of the product")
    category:Optional[str] = Field(None, max_length=50, description="Category of the product")
    tags:Optional[list[str]] = Field(None, description="Tags associated with the product")

class ProductResponse(BaseModel):
    id:str
    name:str
    description:Optional[str]
    price:float
    stock:int
    category:Optional[str]
    tags:list[str]
    is_active:bool
    created_at:datetime
    updated_at:datetime

    class Config:
        from_attributes = True ## enable ORM mode for compatibility with Beanie documents

## response schema for paginated product list
class ProductList(BaseModel):
    products:list[ProductResponse]
    total:int
    page:int
    size:int