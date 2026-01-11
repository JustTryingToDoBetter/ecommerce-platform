

## post /app/routers/product.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from beanie import PydanticObjectId
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductList
from app.utils.exceptions import NotFoundException
from app.models.user import User
from app.services.auth import get_current_superuser
from app.config import get_settings
settings = get_settings()
router = APIRouter()

def product_to_response(product: Product) -> ProductResponse:
    """Convert Product document to ProductResponse."""
    return ProductResponse(
        id=str(product.id),
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        category=product.category,
        tags=product.tags,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at
    )

## admin only
@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_superuser),
):
    """Create a new product."""
    product = Product(**product_data.dict())
    await product.insert()
    return product_to_response(product)



## list products with pagination
@router.get("/", response_model=ProductList, status_code=200)
async def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Number of products per page"),
    search: Optional[str] = Query(None, description="Search term for product name or description"),
):
    """List products with pagination and optional search."""
    if search:
        products_query = Product.find(
            {"$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
            ]}
        )
    else:
        products_query = Product.find()
    total = await products_query.count()
    products = await products_query.skip((page - 1) * size).limit(size).to_list()
    return ProductList(
        products=[product_to_response(prod) for prod in products],
        total=total,
        page=page,
        size=size,
    )

@router.get("/{product_id}", response_model=ProductResponse, status_code=200)
async def get_product(
    product_id: PydanticObjectId,
):
    """Get product details by ID."""
    product = await Product.get(product_id)
    if not product:
        raise NotFoundException(detail="Product not found")
    return product_to_response(product)
## update product
@router.put("/{product_id}", response_model=ProductResponse, status_code=200)
async def update_product(
    product_id: PydanticObjectId,
    product_data: ProductUpdate
):
    product = await Product.get(product_id)
    if not product:
        raise NotFoundException(detail="Product not found")
    update_data = product_data.dict(exclude_unset=True) ## only update provided fields
    for key, value in update_data.items():
        setattr(product, key, value)
    await product.save()
    return product_to_response(product)
    

## delete product
@router.delete("/{product_id}", status_code=200)
async def delete_product(
    product_id: PydanticObjectId,
):
    product = await Product.get(product_id)
    if not product:
        raise NotFoundException(detail="Product not found")
    await product.delete()
    return {"message": "Product deleted"}