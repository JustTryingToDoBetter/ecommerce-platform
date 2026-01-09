## All endpoints require authentication (user must be logged in)
from fastapi import APIRouter, Depends
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.services.cart import get_cart, add_to_cart, update_cart_item, remove_from_cart, clear_cart
from app.routers.auth import  get_current_user


## Initialize router
router = APIRouter(
    dependencies=[Depends(get_current_user)]
)
## Get current user's cart
@router.get("/", response_model=CartResponse)
async def read_cart(current_user=Depends(get_current_user)):
    return await get_cart(current_user.id)

## Add item to cart
@router.post("/items", response_model=CartResponse)
async def add_item_to_cart(
    item_data: CartItemAdd,
    current_user=Depends(get_current_user)
):
    return await add_to_cart(current_user.id, item_data)

## Update item in cart
@router.put("/cart/items", response_model=CartResponse) 
async def update_item_in_cart(
    item_data: CartItemUpdate,
    current_user=Depends(get_current_user)
):
    return await update_cart_item(current_user.id, item_data)

## remove item from cart 
@router.delete("/", response_model=CartResponse)
async def remove_item_from_cart(
    product_id: int,
    current_user=Depends(get_current_user)
):
    return await remove_from_cart(current_user.id, product_id)

## Clear entire cart
@router.delete("/", response_model=CartResponse)
async def clear_user_cart(current_user=Depends(get_current_user)):
    return await clear_cart(current_user.id)