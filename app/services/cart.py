
import datetime
from app.models.cart import Cart
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.services.product import get_product


## get cart
async def get_cart(user_id: str) -> CartResponse:
    cart = await Cart.find_one(Cart.user_id == user_id) ## fetch cart by user_id
    if not cart:
        return CartResponse(items=[], total_price=0.0)  ## return empty cart if not found
    total_price = sum(item.price * item.quantity for item in cart.items) ## calculate total price
    return CartResponse(items=cart.items, total_price=total_price) ## return cart response

## add item to cart
async def add_to_cart(user_id: str, item_data: CartItemAdd) -> CartResponse:
    cart = await Cart.find_one(Cart.user_id == user_id) ## fetch cart by user_id
    product = await get_product(item_data.product_id) ## fetch product details
    if not cart:
        cart = Cart(user_id=user_id, items=[])  ## create new cart if not found
    if product.stock < item_data.quantity:
        raise ValueError("Insufficient stock for the product")  ## raise error if insufficient stock
    
    # Check if item already in cart
    for item in cart.items:
        if item.product_id == item_data.product_id:
            item.quantity += item_data.quantity  ## update quantity if exists
            break
    else:
        cart.items.append(  ## add new item to cart
            {
                "product_id": item_data.product_id,
                "quantity": item_data.quantity,
                "price": product.price,
            }
        )
    
    cart.updated_at = datetime.datetime.utcnow()  ## update timestamp
    await cart.save()  ## save cart to db
    
    total_price = sum(item.price * item.quantity for item in cart.items) ## calculate total price
    return CartResponse(items=cart.items, total_price=total_price) ## return updated cart response
## update cart item
async def update_cart_item(user_id: str, item_data: CartItemUpdate) -> CartResponse:
    cart = await Cart.find_one(Cart.user_id == user_id) ## fetch cart by user_id
    if not cart:
        raise ValueError("Cart not found")  ## raise error if cart not found
    
    for item in cart.items:
        if item.product_id == item_data.product_id:
            item.quantity = item_data.quantity  ## update quantity
            break
    else:
        raise ValueError("Item not found in cart")  ## raise error if item not found
    
    cart.updated_at = datetime.datetime.utcnow()  ## update timestamp
    await cart.save()  ## save cart to db
    
    total_price = sum(item.price * item.quantity for item in cart.items) ## calculate total price
    return CartResponse(items=cart.items, total_price=total_price) ## return updated cart response

## remove from cart
async def remove_from_cart(user_id: str, product_id: int) -> CartResponse:
    cart = await Cart.find_one(Cart.user_id == user_id) ## fetch cart by user_id
    if not cart:
        raise ValueError("Cart not found")  ## raise error if cart not found
    
    cart.items = [item for item in cart.items if item.product_id != product_id]  ## remove item from cart
    
    cart.updated_at = datetime.datetime.utcnow()  ## update timestamp
    await cart.save()  ## save cart to db
    
    total_price = sum(item.price * item.quantity for item in cart.items) ## calculate total price
    return CartResponse(items=cart.items, total_price=total_price) ## return updated cart response


## clear cart
async def clear_cart(user_id: str) -> CartResponse:
    cart = await Cart.find_one(Cart.user_id == user_id) ## fetch cart by user_id
    if not cart:
        raise ValueError("Cart not found")  ## raise error if cart not found
    
    cart.items = []  ## clear all items from cart
    
    cart.updated_at = datetime.datetime.utcnow()  ## update timestamp
    await cart.save()  ## save cart to db
    
    return CartResponse(items=[], total_price=0.0)  ## return empty cart response

## get cart total
async def get_cart_total(user_id: str) -> float:
    cart = await Cart.find_one(Cart.user_id == user_id) ## fetch cart by user_id
    if not cart:
        return 0.0  ## return 0 if cart not found
    total_price = sum(item.price * item.quantity for item in cart.items) ## calculate total price
    return total_price