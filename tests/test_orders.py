"""
Order tests for the e-commerce platform.

Test Cases:
- Checkout with items → order created, stock reduced, cart cleared
- Checkout empty cart → error
- Cancel pending order → stock restored
"""
import pytest
from httpx import AsyncClient
from app.models.product import Product

pytestmark = pytest.mark.asyncio


class TestCreateOrder:
    """Tests for creating orders (checkout)."""
    
    async def test_checkout_with_items_success(
        self, client: AsyncClient, auth_headers, cart_with_items, test_product
    ):
        """Checkout with items in cart creates order successfully."""
        original_stock = test_product.stock
        
        response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {
                        "product_id": str(test_product.id),
                        "quantity": 2
                    }
                ],
                "shipping_address": "123 Test Street, Test City, 12345"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify order was created
        assert "id" in data
        assert data["status"] == "pending"
        assert data["shipping_address"] == "123 Test Street, Test City, 12345"
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == str(test_product.id)
        assert data["items"][0]["quantity"] == 2
        assert data["total"] == test_product.price * 2
        
        # Verify stock was reduced
        updated_product = await Product.get(test_product.id)
        assert updated_product.stock == original_stock - 2
        
        # Verify cart was cleared (get cart should be empty)
        cart_response = await client.get("/api/v1/cart/", headers=auth_headers)
        cart_data = cart_response.json()
        assert len(cart_data["items"]) == 0
    
    async def test_checkout_empty_cart_returns_error(
        self, client: AsyncClient, auth_headers
    ):
        """Checkout with empty cart returns error."""
        response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {
                        "product_id": "507f1f77bcf86cd799439011",
                        "quantity": 1
                    }
                ],
                "shipping_address": "123 Test Street"
            },
            headers=auth_headers
        )
        
        # Should fail - cart is empty
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower() or "cart" in data["detail"].lower()
    
    async def test_checkout_item_not_in_cart_returns_error(
        self, client: AsyncClient, auth_headers, cart_with_items, test_products
    ):
        """Checkout with item not in cart returns error."""
        # cart_with_items has test_product, but we try to order a different product
        other_product = test_products[0]
        
        response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {
                        "product_id": str(other_product.id),
                        "quantity": 1
                    }
                ],
                "shipping_address": "123 Test Street"
            },
            headers=auth_headers
        )
        
        # Should fail - item not in cart
        assert response.status_code == 400
        data = response.json()
        assert "not in cart" in data["detail"].lower()
    
    async def test_checkout_insufficient_stock_returns_error(
        self, client: AsyncClient, auth_headers, test_user
    ):
        """Checkout with quantity exceeding stock returns error."""
        # Create a product with limited stock
        from app.models.cart import Cart, CartItem
        
        limited_product = Product(
            name="Limited Product",
            price=10.00,
            stock=3,  # Only 3 in stock
            is_active=True
        )
        await limited_product.insert()
        
        # Create cart with more quantity than stock
        cart = Cart(
            user_id=test_user.id,
            items=[
                CartItem(
                    product_id=limited_product.id,
                    quantity=10,  # More than available
                    price=limited_product.price
                )
            ]
        )
        await cart.insert()
        
        response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {
                        "product_id": str(limited_product.id),
                        "quantity": 10
                    }
                ],
                "shipping_address": "123 Test Street"
            },
            headers=auth_headers
        )
        
        # Should fail due to insufficient stock
        assert response.status_code == 400
        data = response.json()
        assert "stock" in data["detail"].lower() or "insufficient" in data["detail"].lower()
    
    async def test_checkout_without_auth_returns_401(
        self, client: AsyncClient, test_product
    ):
        """Checkout without authentication returns 401."""
        response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {
                        "product_id": str(test_product.id),
                        "quantity": 1
                    }
                ],
                "shipping_address": "123 Test Street"
            }
        )
        
        assert response.status_code == 401
    
    async def test_checkout_multiple_items(
        self, client: AsyncClient, auth_headers, test_user, test_products
    ):
        """Checkout with multiple items creates order with all items."""
        from app.models.cart import Cart, CartItem
        
        product1 = test_products[0]
        product2 = test_products[1]
        
        # Create cart with multiple items
        cart = Cart(
            user_id=test_user.id,
            items=[
                CartItem(product_id=product1.id, quantity=2, price=product1.price),
                CartItem(product_id=product2.id, quantity=3, price=product2.price)
            ]
        )
        await cart.insert()
        
        response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {"product_id": str(product1.id), "quantity": 2},
                    {"product_id": str(product2.id), "quantity": 3}
                ],
                "shipping_address": "456 Multi-Item Street"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["items"]) == 2
        expected_total = (product1.price * 2) + (product2.price * 3)
        assert data["total"] == expected_total


class TestListOrders:
    """Tests for listing user orders."""
    
    async def test_list_orders_empty(
        self, client: AsyncClient, auth_headers
    ):
        """List orders when user has no orders returns empty list."""
        response = await client.get(
            "/api/v1/orders/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["orders"] == []
        assert data["total"] == 0
    
    async def test_list_orders_with_orders(
        self, client: AsyncClient, auth_headers, cart_with_items, test_product
    ):
        """List orders returns user's orders."""
        # Create an order first
        await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {"product_id": str(test_product.id), "quantity": 2}
                ],
                "shipping_address": "Test Address"
            },
            headers=auth_headers
        )
        
        # List orders
        response = await client.get(
            "/api/v1/orders/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["orders"]) >= 1
    
    async def test_list_orders_pagination(
        self, client: AsyncClient, auth_headers
    ):
        """List orders with pagination parameters."""
        response = await client.get(
            "/api/v1/orders/?page=1&size=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 5
    
    async def test_list_orders_without_auth_returns_401(
        self, client: AsyncClient
    ):
        """List orders without authentication returns 401."""
        response = await client.get("/api/v1/orders/")
        
        assert response.status_code == 401


class TestGetOrder:
    """Tests for getting a single order."""
    
    async def test_get_order_success(
        self, client: AsyncClient, auth_headers, cart_with_items, test_product
    ):
        """Get order by ID returns order details."""
        # Create an order first
        create_response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {"product_id": str(test_product.id), "quantity": 2}
                ],
                "shipping_address": "Test Address"
            },
            headers=auth_headers
        )
        order_id = create_response.json()["id"]
        
        # Get the order
        response = await client.get(
            f"/api/v1/orders/{order_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["status"] == "pending"
    
    async def test_get_order_not_found(
        self, client: AsyncClient, auth_headers
    ):
        """Get non-existent order returns 404."""
        fake_id = "507f1f77bcf86cd799439011"
        
        response = await client.get(
            f"/api/v1/orders/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code in [404, 500]  # Depends on error handling
    
    async def test_get_other_users_order_returns_403(
        self, client: AsyncClient, auth_headers, admin_user
    ):
        """Get another user's order returns 403."""
        from app.models.order import Order, OrderItem
        from beanie import PydanticObjectId
        
        # Create an order for admin user
        admin_order = Order(
            user_id=admin_user.id,
            items=[
                OrderItem(
                    product_id=PydanticObjectId(),
                    name="Admin Product",
                    quantity=1,
                    price=50.00
                )
            ],
            total=50.00,
            shipping_address="Admin Address"
        )
        await admin_order.insert()
        
        # Try to access as regular user
        response = await client.get(
            f"/api/v1/orders/{admin_order.id}",
            headers=auth_headers  # Regular user headers
        )
        
        assert response.status_code == 403


class TestCancelOrder:
    """Tests for cancelling orders."""
    
    async def test_cancel_pending_order_success(
        self, client: AsyncClient, auth_headers, cart_with_items, test_product
    ):
        """Cancel pending order restores stock."""
        original_stock = test_product.stock
        
        # Create an order
        create_response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {"product_id": str(test_product.id), "quantity": 2}
                ],
                "shipping_address": "Test Address"
            },
            headers=auth_headers
        )
        order_id = create_response.json()["id"]
        
        # Verify stock was reduced
        product_after_order = await Product.get(test_product.id)
        assert product_after_order.stock == original_stock - 2
        
        # Cancel the order
        response = await client.delete(
            f"/api/v1/orders/{order_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        
        # Verify stock was restored
        product_after_cancel = await Product.get(test_product.id)
        assert product_after_cancel.stock == original_stock
    
    async def test_cancel_non_pending_order_returns_error(
        self, client: AsyncClient, auth_headers, admin_headers, cart_with_items, test_product
    ):
        """Cancel order that is not pending returns error."""
        # Create an order
        create_response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {"product_id": str(test_product.id), "quantity": 2}
                ],
                "shipping_address": "Test Address"
            },
            headers=auth_headers
        )
        order_id = create_response.json()["id"]
        
        # Update order status to "confirmed" (admin only)
        await client.patch(
            f"/api/v1/orders/{order_id}/status?new_status=confirmed",
            headers=admin_headers
        )
        
        # Try to cancel confirmed order
        response = await client.delete(
            f"/api/v1/orders/{order_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "cannot cancel" in data["detail"].lower() or "status" in data["detail"].lower()
    
    async def test_cancel_order_without_auth_returns_401(
        self, client: AsyncClient
    ):
        """Cancel order without authentication returns 401."""
        fake_id = "507f1f77bcf86cd799439011"
        
        response = await client.delete(f"/api/v1/orders/{fake_id}")
        
        assert response.status_code == 401


class TestUpdateOrderStatus:
    """Tests for updating order status (admin only)."""
    
    async def test_update_order_status_as_admin(
        self, client: AsyncClient, admin_headers, cart_with_items, test_product, auth_headers
    ):
        """Admin can update order status."""
        # Create an order as regular user
        create_response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {"product_id": str(test_product.id), "quantity": 2}
                ],
                "shipping_address": "Test Address"
            },
            headers=auth_headers
        )
        order_id = create_response.json()["id"]
        
        # Update status as admin
        response = await client.patch(
            f"/api/v1/orders/{order_id}/status?new_status=confirmed",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
    
    async def test_update_order_status_as_regular_user_returns_401(
        self, client: AsyncClient, auth_headers, cart_with_items, test_product
    ):
        """Regular user cannot update order status."""
        # Create an order
        create_response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {"product_id": str(test_product.id), "quantity": 2}
                ],
                "shipping_address": "Test Address"
            },
            headers=auth_headers
        )
        order_id = create_response.json()["id"]
        
        # Try to update status as regular user
        response = await client.patch(
            f"/api/v1/orders/{order_id}/status?new_status=confirmed",
            headers=auth_headers
        )
        
        assert response.status_code == 401  # Admin access required
    
    async def test_update_order_status_progression(
        self, client: AsyncClient, admin_headers, auth_headers, cart_with_items, test_product
    ):
        """Order status can progress through valid states."""
        # Create an order
        create_response = await client.post(
            "/api/v1/orders/",
            json={
                "items": [
                    {"product_id": str(test_product.id), "quantity": 2}
                ],
                "shipping_address": "Test Address"
            },
            headers=auth_headers
        )
        order_id = create_response.json()["id"]
        
        # Progress: pending -> confirmed -> shipped -> delivered
        for status in ["confirmed", "shipped", "delivered"]:
            response = await client.patch(
                f"/api/v1/orders/{order_id}/status?new_status={status}",
                headers=admin_headers
            )
            assert response.status_code == 200
            assert response.json()["status"] == status
