import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.order import Order, OrderItem, OrderStatus
from schemas.order import OrderCreate, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])


def _generate_order_uid() -> str:
    now = datetime.utcnow().strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6].upper()
    return f"ORD-{now}-{short}"


@router.get("/", response_model=list[OrderOut])
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all orders for the current user."""
    return (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific order by ID."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderOut)
def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new order with items."""
    total = sum(item.price * item.quantity for item in data.items)
    order = Order(
        order_uid=_generate_order_uid(),
        user_id=current_user.id,
        status=OrderStatus.pending,
        total=total,
        pharmacy=data.pharmacy,
        payment_method=data.payment_method,
    )
    db.add(order)
    db.flush()

    for item in data.items:
        db.add(
            OrderItem(
                order_id=order.id,
                medicine_id=item.medicine_id,
                name=item.name,
                quantity=item.quantity,
                price=item.price,
            )
        )

    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update order status."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order
