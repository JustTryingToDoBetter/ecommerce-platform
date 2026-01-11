from beanie import PydanticObjectId
from app.schemas.order import OrderResponse, OrderCreate, OrderItemResponse
from app.models.order import Order, OrderItem, OrderStatus
from app.services.cart import get_cart, clear_cart
from app.services.product import get_product, update_product
from typing import List

def build_order_response(order: Order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        items=[OrderItemResponse(
            product_id=item.product_id,
            name=item.name,
            quantity=item.quantity,
            price=item.price
        ) for item in order.items],
        status=order.status,
        total=order.total,
        shipping_address=order.shipping_address,
        created_at=order.created_at,
        updated_at=order.updated_at
    )

async def create_order(user_id: PydanticObjectId, order_data: OrderCreate) -> OrderResponse:
    # Fetch user's actual cart
    user_cart = await get_cart(user_id)
    
    if not user_cart.items:
        raise ValueError("Cart is empty")
    
    # Validate items exist in cart
    cart_product_ids = {item.product_id for item in user_cart.items}
    for item in order_data.items:
        if item.product_id not in cart_product_ids:
            raise ValueError(f"Item {item.product_id} not in cart")
    
    # Build order items with product details
    order_items = []
    total = 0.0
    
    for item in order_data.items:
        product = await get_product(item.product_id)
        if product.stock < item.quantity:
            raise ValueError(f"Insufficient stock for {product.name}")
        
        order_items.append(OrderItem(
            product_id=item.product_id,
            name=product.name,
            quantity=item.quantity,
            price=product.price
        ))
        total += product.price * item.quantity
    
    # Create and save order
    order = Order(
        user_id=user_id,
        items=order_items,
        total=total,
        shipping_address=order_data.shipping_address
    )
    await order.save()
    
    # Update stock for each product
    for item in order_items:
        await update_product(item.product_id, -item.quantity)
    
    # Clear the cart
    await clear_cart(user_id)
    
    # Build response
    return build_order_response(order)


async def get_order(order_id: PydanticObjectId) -> OrderResponse:
    order = await Order.get(order_id)
    if not order:
        raise Exception("order not found")
    return build_order_response(order)

async def list_user_orders(user_id: PydanticObjectId) -> List[OrderResponse]:
    orders = await Order.find(Order.user_id == user_id).to_list()

    return [
        build_order_response(order)
        for order in orders
    ]

async def update_order_status(order_id: PydanticObjectId ,new_status: OrderStatus) -> OrderResponse:

    order = await Order.get(order_id)    
    if not order:
        raise ValueError("Order not found")
    
    order.status = new_status
    await order.save()
    
    return build_order_response(order)


async def cancel_order(order_id : PydanticObjectId):
    order = await Order.get(order_id)
    if not order:
        raise ValueError("Order not found")

   # Only pending orders can be cancelled
    if order.status != OrderStatus.PENDING:
        raise ValueError(f"Cannot cancel order with status: {order.status.value}")
    
    # Restore stock for each item
    for item in order.items:
        await update_product(item.product_id, item.quantity)  # Add back stock
    
    order.status = OrderStatus.CANCELLED
    await order.save()
    
    return build_order_response(order)