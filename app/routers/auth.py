from datetime import timedelta
from typing import Optional
from beanie import PydanticObjectId
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.models.user import User
from app.schemas.user import UserCreate, Token
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from app.utils.exceptions import (
    UnauthorizedException,
    ConflictException,
    NotFoundException,
)
from app.config import get_settings

settings = get_settings()

# OAuth2 scheme for token extraction from headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def register_user(user_data: UserCreate) -> User:
    """Register a new user."""
    # Check if user already exists
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise ConflictException("User with this email already exists")
    
    # Create new user with hashed password
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
    )
    await user.insert()
    
    return user


async def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password."""
    user = await User.find_one(User.email == email)
    
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def login_user(email: str, password: str) -> Token:
    """Login user and return JWT token."""
    user = await authenticate_user(email, password)
    
    if not user:
        raise UnauthorizedException("Incorrect email or password")
    
    if not user.is_active:
        raise UnauthorizedException("User account is disabled")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    
    return Token(access_token=access_token)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token. Use as a dependency."""
    payload = decode_access_token(token)
    
    if payload is None:
        raise UnauthorizedException("Invalid or expired token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Invalid token payload")
    
    user = await User.get(PydanticObjectId(user_id))
    
    if user is None:
        raise NotFoundException("User not found")
    
    if not user.is_active:
        raise UnauthorizedException("User account is disabled")
    
    return user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """Get current superuser. Use as a dependency for admin-only routes."""
    if not current_user.is_superuser:
        raise UnauthorizedException("Admin access required")
    return current_user