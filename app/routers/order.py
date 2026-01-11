from fastapi import APIRouter, HTTPException, Depends, Query
from beanie import PydanticObjectId
from app.config import get_settings
from app.schemas.order import OrderResponse, OrderCreate, OrderList
from app.models.order import OrderStatus
from app.models.user import User
from app.services.auth import get_current_user, get_current_superuser
from app.services.order import (
    create_order as create_order_service,
    get_order as get_order_service,
    list_user_orders,
    update_order_status,
    cancel_order as cancel_order_service
)

settings = get_settings()
router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=201)
async def create_order_endpoint(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user)
):
    try:
        return await create_order_service(current_user.id, order_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=OrderList, status_code=200)
async def list_orders_endpoint(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    orders = await list_user_orders(current_user.id)
    start = (page - 1) * size
    paginated = orders[start:start + size]
    return OrderList(orders=paginated, total=len(orders), page=page, size=size)


@router.get("/{order_id}", response_model=OrderResponse, status_code=200)
async def get_order_endpoint(
    order_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    try:
        order = await get_order_service(order_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
    if order.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not your order")
    
    return order


@router.patch("/{order_id}/status", response_model=OrderResponse, status_code=200)
async def update_status_endpoint(
    order_id: PydanticObjectId,
    new_status: OrderStatus,
    current_user: User = Depends(get_current_superuser)
):
    try:
        return await update_order_status(order_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{order_id}", response_model=OrderResponse, status_code=200)
async def cancel_order_endpoint(
    order_id: PydanticObjectId,
    current_user: User = Depends(get_current_user)
):
    try:
        return await cancel_order_service(order_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))