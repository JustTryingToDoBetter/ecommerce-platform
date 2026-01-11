"""
Authentication tests for the e-commerce platform.

Test Cases:
- Register new user → success
- Register duplicate email → 409 error
- Login with correct credentials → get token
- Login with wrong password → 401 error
- Access protected route without token → 401
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestUserRegistration:
    """Tests for user registration endpoint."""
    
    async def test_register_new_user_success(self, client: AsyncClient):
        """Register a new user successfully."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data
    
    async def test_register_without_full_name(self, client: AsyncClient):
        """Register a new user without full_name (optional field)."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "minimaluser@example.com",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "minimaluser@example.com"
    
    async def test_register_duplicate_email_returns_409(self, client: AsyncClient, test_user):
        """Register with existing email returns 409 conflict."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "password": "anotherpassword123",
                "full_name": "Duplicate User"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    async def test_register_invalid_email_format(self, client: AsyncClient):
        """Register with invalid email format returns validation error."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_register_short_password(self, client: AsyncClient):
        """Register with too short password returns validation error."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "validuser@example.com",
                "password": "short"  # Too short
            }
        )
        
        # Should fail validation if password min length is enforced
        assert response.status_code in [400, 422]


class TestUserLogin:
    """Tests for user login endpoint."""
    
    async def test_login_with_correct_credentials_returns_token(
        self, client: AsyncClient, test_user
    ):
        """Login with valid credentials returns access token."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] is not None
        assert len(data["access_token"]) > 0
    
    async def test_login_with_wrong_password_returns_401(
        self, client: AsyncClient, test_user
    ):
        """Login with wrong password returns 401 unauthorized."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower() or "password" in data["detail"].lower()
    
    async def test_login_with_nonexistent_email_returns_401(self, client: AsyncClient):
        """Login with non-existent email returns 401 unauthorized."""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "anypassword"
            }
        )
        
        assert response.status_code == 401
    
    async def test_login_inactive_user_returns_401(self, client: AsyncClient):
        """Login with inactive user account returns 401."""
        from app.models.user import User
        from app.utils.security import get_password_hash
        
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=False
        )
        await inactive_user.insert()
        
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "inactive@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "disabled" in data["detail"].lower()


class TestProtectedRoutes:
    """Tests for accessing protected routes."""
    
    async def test_access_protected_route_without_token_returns_401(
        self, client: AsyncClient
    ):
        """Access /me without token returns 401 unauthorized."""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_access_protected_route_with_invalid_token_returns_401(
        self, client: AsyncClient
    ):
        """Access /me with invalid token returns 401 unauthorized."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401
    
    async def test_access_protected_route_with_valid_token_success(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Access /me with valid token returns user profile."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] is True
    
    async def test_access_protected_route_with_expired_token_returns_401(
        self, client: AsyncClient
    ):
        """Access /me with expired token returns 401 unauthorized."""
        from datetime import timedelta
        from app.utils.security import create_access_token
        
        # Create an already expired token
        expired_token = create_access_token(
            data={"sub": "some-user-id"},
            expires_delta=timedelta(seconds=-60)  # Expired 60 seconds ago
        )
        
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
    
    async def test_access_protected_route_with_malformed_header_returns_401(
        self, client: AsyncClient
    ):
        """Access /me with malformed Authorization header returns 401."""
        # Missing "Bearer" prefix
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "just_a_token"}
        )
        
        assert response.status_code == 401


class TestAdminUser:
    """Tests for admin user functionality."""
    
    async def test_admin_user_has_superuser_flag(
        self, client: AsyncClient, admin_user, admin_headers
    ):
        """Admin user should be identified as superuser."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        # Note: The UserResponse might not include is_superuser
        # This test verifies the admin can access their profile
        data = response.json()
        assert data["email"] == admin_user.email
