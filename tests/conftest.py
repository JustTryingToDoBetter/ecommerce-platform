"""
Test configuration and fixtures for the e-commerce platform.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from mongomock_motor import AsyncMongoMockClient

from app.main import app
from app.models.user import User
from app.models.product import Product
from app.models.cart import Cart
from app.models.order import Order
from app.utils.security import get_password_hash, create_access_token


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Set up a mock MongoDB database for tests."""
    client = AsyncMongoMockClient()
    await init_beanie(
        database=client["test_ecommerce"],
        document_models=[User, Product, Cart, Order]
    )
    yield
    # Cleanup after each test
    await User.delete_all()
    await Product.delete_all()
    await Cart.delete_all()
    await Order.delete_all()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user() -> User:
    """Create a regular test user."""
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    await user.insert()
    return user


@pytest.fixture
async def admin_user() -> User:
    """Create an admin/superuser test user."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    await user.insert()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for regular user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    """Create authentication headers for admin user."""
    token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_product() -> Product:
    """Create a test product."""
    product = Product(
        name="Test Product",
        description="A test product description",
        price=29.99,
        stock=100,
        category="Electronics",
        tags=["test", "sample"],
        is_active=True
    )
    await product.insert()
    return product


@pytest.fixture
async def test_products() -> list[Product]:
    """Create multiple test products."""
    products = []
    for i in range(5):
        product = Product(
            name=f"Product {i+1}",
            description=f"Description for product {i+1}",
            price=10.00 + i * 5,
            stock=50 + i * 10,
            category="Test Category",
            tags=["test"],
            is_active=True
        )
        await product.insert()
        products.append(product)
    return products


@pytest.fixture
async def cart_with_items(test_user: User, test_product: Product) -> Cart:
    """Create a cart with items for the test user."""
    from app.models.cart import CartItem
    cart = Cart(
        user_id=test_user.id,
        items=[
            CartItem(
                product_id=test_product.id,
                quantity=2,
                price=test_product.price
            )
        ]
    )
    await cart.insert()
    return cart
