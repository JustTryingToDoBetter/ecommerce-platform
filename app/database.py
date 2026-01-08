from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import get_settings

# Import all your document models here
from app.models.user import User
from app.models.product import Product
from app.models.cart import Cart
from app.models.order import Order


async def init_db():
    """Initialize database connection and Beanie ODM."""
    settings = get_settings()
    
    client = AsyncIOMotorClient(settings.mongodb_url)
    
    await init_beanie(
        database=client[settings.database_name],
        document_models=[
            User,
            Product,
            Cart,
            Order,
        ]
    )