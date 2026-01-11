from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database import init_db
from app.config import get_settings
from slowapi.middleware import SlowAPIMiddleware
# Import routers
from app.routers import auth, product, cart, order
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await init_db()
    print("✅ Database connected!")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="E-commerce Platform API",
    description="A scalable e-commerce backend API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
# Register routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(product.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(cart.router, prefix="/api/v1/cart", tags=["Cart"])
app.include_router(order.router, prefix="/api/v1/orders", tags=["Orders"])


@app.get("/")
async def root():
    return {"message": "Welcome to the E-commerce API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}