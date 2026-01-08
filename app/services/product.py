
from schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductList
from models.product import Product

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

async def get_product(product_id: str) -> ProductResponse:
    ## get product by id
    product = await Product.get(product_id)
    if not product:
        raise Exception("Product not found")  ## custom exception can be used
    return ProductResponse.from_orm(product)

## list products with pagination
async def list_products(page: int = 1, size: int = 10) -> ProductList:
    skip = (page - 1) * size
    products_cursor = Product.find().skip(skip).limit(size) ## query with pagination
    products = await products_cursor.to_list() ## convert cursor to list
    total = await Product.count_documents({}) ## total count for pagination
    
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
    
    return ProductUpdate(
        name=product_data.name or product.name,
        description=product_data.description or product.description,
        price=product_data.price if product_data.price is not None else product.price,
        stock=product_data.stock if product_data.stock is not None else product.stock,
        category=product_data.category or product.category,
        tags=product_data.tags if product_data.tags is not None else product.tags,
    )

## delete product

async def delete_product(product_id: str) -> None:
    product = await Product.get(product_id)
    if not product:
        raise Exception("Product not found")  ## custom exception can be used
    
    await product.delete()  ## delete from db
    return ProductResponse.from_orm(product)
