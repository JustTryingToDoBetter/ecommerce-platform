
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductList
from app.models.product import Product
from beanie import PydanticObjectId

## create a product
async def create_product(product_data: ProductCreate) -> ProductResponse:
    ## create object
    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock,
        category=product_data.category,
        tags=product_data.tags or [],
    )
    
    await product.insert() ## save to db
    return ProductResponse.from_orm(product) ## return response schema

## get proudct

async def get_product(product_id: str) -> Product:
    ## get product by id
    product = await Product.get(product_id)
    if not product:
        raise Exception("Product not found")  ## custom exception can be used
    return product

## list products with pagination
async def list_products(page: int = 1, size: int = 10) -> ProductList:
    skip = (page - 1) * size
    products_cursor = Product.find().skip(skip).limit(size) ## query with pagination
    products = await products_cursor.to_list() ## convert cursor to list
    total = await Product.find().count() ## total count for pagination
    
    return ProductList(
        products=[ProductResponse.from_orm(prod) for prod in products], ## map to response schema
        total=total,
        page=page,
        size=size,
    )

## upudate product

async def update_product(product_id: str, product_data: ProductUpdate) -> ProductResponse:
    product = await Product.get(product_id)
    if not product:
        raise Exception("Product not found")  ## custom exception can be used
    
    # Update fields if provided
    if product_data.name is not None:
        product.name = product_data.name
    if product_data.description is not None:
        product.description = product_data.description
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.stock is not None:
        product.stock = product_data.stock
    if product_data.category is not None:
        product.category = product_data.category
    if product_data.tags is not None:
        product.tags = product_data.tags
    
    await product.save()  ## save changes to db
    return ProductResponse.from_orm(product)

## update product stock by quantity delta
async def update_product_stock(product_id: PydanticObjectId, quantity_delta: int) -> Product:
    """Update product stock by a quantity delta (positive to add, negative to reduce)."""
    product = await Product.get(product_id)
    if not product:
        raise Exception("Product not found")
    
    product.stock += quantity_delta
    if product.stock < 0:
        raise ValueError("Insufficient stock")
    
    await product.save()
    return product

## delete product

async def delete_product(product_id: str) -> None:
    product = await Product.get(product_id)
    if not product:
        raise Exception("Product not found")  ## custom exception can be used
    
    await product.delete()  ## delete from db
    return ProductResponse.from_orm(product)

