"""
Cart tests for the e-commerce platform.

Test Cases:
- Add item to cart
- Add same item again → quantity increases
- Remove item from cart
"""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestGetCart:
    """Tests for getting the user's cart."""
    
    async def test_get_cart_unauthenticated_returns_401(
        self, client: AsyncClient
    ):
        """Get cart without authentication returns 401."""
        response = await client.get("/api/v1/cart/")
        
        assert response.status_code == 401
    
    async def test_get_cart_empty_cart(
        self, client: AsyncClient, auth_headers
    ):
        """Get cart when cart is empty returns empty cart."""
        response = await client.get(
            "/api/v1/cart/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_price"] == 0.0
    
    async def test_get_cart_with_items(
        self, client: AsyncClient, auth_headers, cart_with_items, test_product
    ):
        """Get cart returns cart with items."""
        response = await client.get(
            "/api/v1/cart/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == str(test_product.id)
        assert data["items"][0]["quantity"] == 2
        assert data["total_price"] == test_product.price * 2


class TestAddToCart:
    """Tests for adding items to cart."""
    
    async def test_add_item_to_cart_success(
        self, client: AsyncClient, auth_headers, test_product
    ):
        """Add item to empty cart succeeds."""
        response = await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": 2
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == str(test_product.id)
        assert data["items"][0]["quantity"] == 2
        assert data["items"][0]["price"] == test_product.price
        assert data["total_price"] == test_product.price * 2
    
    async def test_add_same_item_increases_quantity(
        self, client: AsyncClient, auth_headers, test_product
    ):
        """Add same item again increases quantity instead of duplicating."""
        # Add item first time
        await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": 2
            },
            headers=auth_headers
        )
        
        # Add same item again
        response = await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": 3
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should have only one item with combined quantity
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 5  # 2 + 3
        assert data["total_price"] == test_product.price * 5
    
    async def test_add_different_items_to_cart(
        self, client: AsyncClient, auth_headers, test_products
    ):
        """Add multiple different items to cart."""
        product1 = test_products[0]
        product2 = test_products[1]
        
        # Add first product
        await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(product1.id),
                "quantity": 1
            },
            headers=auth_headers
        )
        
        # Add second product
        response = await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(product2.id),
                "quantity": 2
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        
        # Verify total price
        expected_total = product1.price * 1 + product2.price * 2
        assert data["total_price"] == expected_total
    
    async def test_add_item_without_auth_returns_401(
        self, client: AsyncClient, test_product
    ):
        """Add item without authentication returns 401."""
        response = await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": 1
            }
        )
        
        assert response.status_code == 401
    
    async def test_add_item_insufficient_stock(
        self, client: AsyncClient, auth_headers, test_product
    ):
        """Add item with quantity exceeding stock returns error."""
        response = await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": 999  # More than available stock (100)
            },
            headers=auth_headers
        )
        
        # Should fail due to insufficient stock
        assert response.status_code in [400, 422, 500]
    
    async def test_add_item_invalid_product_id(
        self, client: AsyncClient, auth_headers
    ):
        """Add item with non-existent product ID returns error."""
        fake_id = "507f1f77bcf86cd799439011"
        
        response = await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": fake_id,
                "quantity": 1
            },
            headers=auth_headers
        )
        
        # Should fail due to product not found
        assert response.status_code in [400, 404, 500]
    
    async def test_add_item_zero_quantity(
        self, client: AsyncClient, auth_headers, test_product
    ):
        """Add item with zero quantity returns validation error."""
        response = await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": 0
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    async def test_add_item_negative_quantity(
        self, client: AsyncClient, auth_headers, test_product
    ):
        """Add item with negative quantity returns validation error."""
        response = await client.post(
            "/api/v1/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": -1
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error


class TestUpdateCartItem:
    """Tests for updating cart items."""
    
    async def test_update_cart_item_quantity(
        self, client: AsyncClient, auth_headers, cart_with_items, test_product
    ):
        """Update item quantity in cart."""
        response = await client.put(
            "/api/v1/cart/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": 5
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"][0]["quantity"] == 5
        assert data["total_price"] == test_product.price * 5
    
    async def test_update_nonexistent_item(
        self, client: AsyncClient, auth_headers, test_product
    ):
        """Update item not in cart returns error."""
        response = await client.put(
            "/api/v1/cart/cart/items",
            json={
                "product_id": str(test_product.id),
                "quantity": 3
            },
            headers=auth_headers
        )
        
        # Should fail - cart doesn't exist or item not in cart
        assert response.status_code in [400, 404, 500]


class TestRemoveFromCart:
    """Tests for removing items from cart."""
    
    async def test_remove_item_from_cart(
        self, client: AsyncClient, auth_headers, cart_with_items, test_product
    ):
        """Remove item from cart succeeds."""
        response = await client.delete(
            f"/api/v1/cart/?product_id={test_product.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # Cart should be empty after removing the only item
        assert len(data["items"]) == 0
        assert data["total_price"] == 0.0
    
    async def test_remove_item_without_auth_returns_401(
        self, client: AsyncClient, test_product
    ):
        """Remove item without authentication returns 401."""
        response = await client.delete(
            f"/api/v1/cart/?product_id={test_product.id}"
        )
        
        assert response.status_code == 401


class TestClearCart:
    """Tests for clearing the entire cart."""
    
    async def test_clear_cart(
        self, client: AsyncClient, auth_headers, cart_with_items
    ):
        """Clear entire cart succeeds."""
        response = await client.delete(
            "/api/v1/cart/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total_price"] == 0.0
    
    async def test_clear_empty_cart(
        self, client: AsyncClient, auth_headers
    ):
        """Clear already empty cart succeeds."""
        response = await client.delete(
            "/api/v1/cart/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
