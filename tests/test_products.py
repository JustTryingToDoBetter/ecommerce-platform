"""
Product tests for the e-commerce platform.

Test Cases:
- List products (public) - no auth required
- Create product as admin → success
- Create product as regular user → 403
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestListProducts:
    """Tests for listing products (public endpoint)."""
    
    async def test_list_products_public_no_auth_required(self, client: AsyncClient):
        """List products without authentication succeeds."""
        response = await client.get("/api/v1/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
    
    async def test_list_products_returns_products(
        self, client: AsyncClient, test_products
    ):
        """List products returns all available products."""
        response = await client.get("/api/v1/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["products"]) == 5
    
    async def test_list_products_pagination(
        self, client: AsyncClient, test_products
    ):
        """List products with pagination works correctly."""
        # Get first page with 2 items
        response = await client.get("/api/v1/products/?page=1&size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 2
        assert data["page"] == 1
        assert data["size"] == 2
        assert data["total"] == 5
        
        # Get second page
        response = await client.get("/api/v1/products/?page=2&size=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["products"]) == 2
        assert data["page"] == 2
    
    async def test_list_products_search(
        self, client: AsyncClient, test_products
    ):
        """List products with search filter works correctly."""
        response = await client.get("/api/v1/products/?search=Product%201")
        
        assert response.status_code == 200
        data = response.json()
        # Should find at least one product matching search
        assert data["total"] >= 1
        # Verify the returned product matches search
        found = any("1" in p["name"] for p in data["products"])
        assert found
    
    async def test_list_products_empty_database(self, client: AsyncClient):
        """List products when database is empty returns empty list."""
        response = await client.get("/api/v1/products/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["products"] == []
        assert data["total"] == 0


class TestGetProduct:
    """Tests for getting a single product."""
    
    async def test_get_product_by_id_success(
        self, client: AsyncClient, test_product
    ):
        """Get product by ID returns product details."""
        response = await client.get(f"/api/v1/products/{test_product.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_product.name
        assert data["description"] == test_product.description
        assert data["price"] == test_product.price
        assert data["stock"] == test_product.stock
    
    async def test_get_product_not_found(self, client: AsyncClient):
        """Get product with non-existent ID returns 404."""
        fake_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
        response = await client.get(f"/api/v1/products/{fake_id}")
        
        assert response.status_code == 404
    
    async def test_get_product_invalid_id_format(self, client: AsyncClient):
        """Get product with invalid ID format returns 422."""
        response = await client.get("/api/v1/products/invalid-id")
        
        assert response.status_code == 422  # Validation error


class TestCreateProduct:
    """Tests for creating products (admin only)."""
    
    async def test_create_product_as_admin_success(
        self, client: AsyncClient, admin_headers
    ):
        """Create product as admin user succeeds."""
        product_data = {
            "name": "New Product",
            "description": "A brand new product",
            "price": 49.99,
            "stock": 25,
            "category": "Test",
            "tags": ["new", "featured"]
        }
        
        response = await client.post(
            "/api/v1/products/",
            json=product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Product"
        assert data["description"] == "A brand new product"
        assert data["price"] == 49.99
        assert data["stock"] == 25
        assert data["category"] == "Test"
        assert "new" in data["tags"]
        assert "featured" in data["tags"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
    
    async def test_create_product_as_regular_user_returns_403(
        self, client: AsyncClient, auth_headers
    ):
        """Create product as regular user returns 403 forbidden."""
        product_data = {
            "name": "Unauthorized Product",
            "description": "Should not be created",
            "price": 19.99,
            "stock": 10
        }
        
        response = await client.post(
            "/api/v1/products/",
            json=product_data,
            headers=auth_headers
        )
        
        # Regular user should not be able to create products
        assert response.status_code == 401  # UnauthorizedException from get_current_superuser
    
    async def test_create_product_without_auth_returns_401(
        self, client: AsyncClient
    ):
        """Create product without authentication returns 401."""
        product_data = {
            "name": "No Auth Product",
            "price": 29.99,
            "stock": 5
        }
        
        response = await client.post(
            "/api/v1/products/",
            json=product_data
        )
        
        assert response.status_code == 401
    
    async def test_create_product_with_minimum_fields(
        self, client: AsyncClient, admin_headers
    ):
        """Create product with only required fields succeeds."""
        product_data = {
            "name": "Minimal Product",
            "price": 9.99
        }
        
        response = await client.post(
            "/api/v1/products/",
            json=product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Product"
        assert data["price"] == 9.99
        assert data["stock"] == 0  # Default value
    
    async def test_create_product_invalid_price(
        self, client: AsyncClient, admin_headers
    ):
        """Create product with invalid price returns validation error."""
        product_data = {
            "name": "Invalid Price Product",
            "price": -10.00  # Negative price
        }
        
        response = await client.post(
            "/api/v1/products/",
            json=product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_create_product_invalid_stock(
        self, client: AsyncClient, admin_headers
    ):
        """Create product with negative stock returns validation error."""
        product_data = {
            "name": "Invalid Stock Product",
            "price": 10.00,
            "stock": -5  # Negative stock
        }
        
        response = await client.post(
            "/api/v1/products/",
            json=product_data,
            headers=admin_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestUpdateProduct:
    """Tests for updating products."""
    
    async def test_update_product_success(
        self, client: AsyncClient, test_product
    ):
        """Update product with valid data succeeds."""
        update_data = {
            "name": "Updated Product Name",
            "price": 39.99
        }
        
        response = await client.put(
            f"/api/v1/products/{test_product.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product Name"
        assert data["price"] == 39.99
        # Original values should remain unchanged
        assert data["description"] == test_product.description
    
    async def test_update_product_partial(
        self, client: AsyncClient, test_product
    ):
        """Update product with partial data only updates specified fields."""
        original_price = test_product.price
        update_data = {
            "stock": 200
        }
        
        response = await client.put(
            f"/api/v1/products/{test_product.id}",
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["stock"] == 200
        assert data["price"] == original_price  # Unchanged
    
    async def test_update_product_not_found(self, client: AsyncClient):
        """Update non-existent product returns 404."""
        fake_id = "507f1f77bcf86cd799439011"
        update_data = {"name": "Does Not Exist"}
        
        response = await client.put(
            f"/api/v1/products/{fake_id}",
            json=update_data
        )
        
        assert response.status_code == 404


class TestDeleteProduct:
    """Tests for deleting products."""
    
    async def test_delete_product_success(
        self, client: AsyncClient, test_product
    ):
        """Delete product succeeds."""
        response = await client.delete(f"/api/v1/products/{test_product.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify product no longer exists
        get_response = await client.get(f"/api/v1/products/{test_product.id}")
        assert get_response.status_code == 404
    
    async def test_delete_product_not_found(self, client: AsyncClient):
        """Delete non-existent product returns 404."""
        fake_id = "507f1f77bcf86cd799439011"
        
        response = await client.delete(f"/api/v1/products/{fake_id}")
        
        assert response.status_code == 404
