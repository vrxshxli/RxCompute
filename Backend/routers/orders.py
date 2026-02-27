import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.order import Order, OrderItem, OrderStatus
from models.medicine import Medicine
from models.notification import NotificationType
from schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from services.notifications import (
    create_notification,
    run_in_background,
    send_push_to_token,
    send_order_email_snapshot,
)
from services.webhooks import dispatch_webhook

router = APIRouter(prefix="/orders", tags=["Orders"])
STAFF_ROLES = {"admin", "pharmacy_store"}


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
    if current_user.role == "warehouse":
        raise HTTPException(status_code=403, detail="Warehouse does not have access to customer orders")
    if current_user.role in STAFF_ROLES:
        return db.query(Order).order_by(Order.created_at.desc()).all()
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
    if current_user.role == "warehouse":
        raise HTTPException(status_code=403, detail="Warehouse does not have access to customer orders")
    query = db.query(Order).filter(Order.id == order_id)
    if current_user.role not in STAFF_ROLES:
        query = query.filter(Order.user_id == current_user.id)
    order = query.first()
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
    med_ids = [item.medicine_id for item in data.items]
    meds = (
        db.query(Medicine)
        .filter(Medicine.id.in_(med_ids))
        .all()
    )
    med_map = {m.id: m for m in meds}
    if len(med_map) != len(set(med_ids)):
        raise HTTPException(status_code=400, detail="One or more medicines were not found")

    rx_missing = []
    for item in data.items:
        med = med_map[item.medicine_id]
        if med.rx_required and not item.prescription_file:
            rx_missing.append(med.name)
    if rx_missing:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Prescription required for one or more medicines",
                "medicines": rx_missing,
            },
        )

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
        med = med_map[item.medicine_id]
        db.add(
            OrderItem(
                order_id=order.id,
                medicine_id=item.medicine_id,
                name=item.name,
                quantity=item.quantity,
                price=item.price,
                dosage_instruction=item.dosage_instruction,
                strips_count=item.strips_count,
                rx_required=med.rx_required,
                prescription_file=item.prescription_file,
            )
        )

    db.commit()
    db.refresh(order)
    order_snapshot = {
        "order_uid": order.order_uid,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "payment_method": order.payment_method,
        "total": order.total,
        "pharmacy": order.pharmacy,
        "items": [{"name": it.name, "quantity": it.quantity, "price": it.price} for it in order.items],
    }

    title = "Order Placed"
    body = f"{order.order_uid} placed successfully. Total {order.total:.2f}"
    create_notification(db, current_user.id, NotificationType.order, title, body, has_action=True)
    db.commit()
    run_in_background(send_push_to_token, current_user.push_token, title, body, current_user.id)
    run_in_background(send_order_email_snapshot, current_user.email, order_snapshot, "RxCompute Order")
    staff_users = db.query(User).filter(User.role.in_(["admin", "pharmacy_store"])).all()
    staff_title = "New Order Received"
    staff_body = f"{order.order_uid} placed by user #{order.user_id}. Total {order.total:.2f}"
    for staff in staff_users:
        create_notification(
            db,
            staff.id,
            NotificationType.order,
            staff_title,
            staff_body,
            has_action=True,
        )
        run_in_background(send_push_to_token, staff.push_token, staff_title, staff_body, staff.id)
        run_in_background(send_order_email_snapshot, staff.email, order_snapshot, "RxCompute New Order")
    db.commit()
    dispatch_webhook(
        db,
        event_type="order_created",
        payload={
            "order_id": order.id,
            "order_uid": order.order_uid,
            "user_id": order.user_id,
            "status": order.status.value,
            "total": order.total,
            "payment_method": order.payment_method,
        },
    )
    return order


@router.put("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update order status."""
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Only staff can update order status")
    query = db.query(Order).filter(Order.id == order_id)
    order = query.first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    old_status = order.status.value if hasattr(order.status, "value") else str(order.status)
    try:
        new_status = OrderStatus(data.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order status")

    if new_status.value == old_status:
        return order

    # Pharmacy must approve first. Admin handles downstream logistics.
    if current_user.role == "pharmacy_store":
        if old_status != OrderStatus.pending.value:
            raise HTTPException(status_code=403, detail="Pharmacy can approve only pending orders")
        if new_status not in {OrderStatus.verified, OrderStatus.cancelled}:
            raise HTTPException(status_code=403, detail="Pharmacy can set only VERIFIED or CANCELLED")
    elif current_user.role == "admin":
        allowed_for_admin = {
            OrderStatus.picking,
            OrderStatus.packed,
            OrderStatus.dispatched,
            OrderStatus.delivered,
            OrderStatus.cancelled,
        }
        if new_status not in allowed_for_admin:
            raise HTTPException(status_code=403, detail="Admin can update only logistics statuses")
        if new_status in {OrderStatus.picking, OrderStatus.packed, OrderStatus.dispatched, OrderStatus.delivered}:
            if old_status not in {
                OrderStatus.verified.value,
                OrderStatus.picking.value,
                OrderStatus.packed.value,
                OrderStatus.dispatched.value,
            }:
                raise HTTPException(status_code=400, detail="Order must be pharmacy-approved first")
    else:
        raise HTTPException(status_code=403, detail="Role cannot update order status")

    # On first approval (pending -> confirmed/verified), reserve stock from inventory.
    if old_status == OrderStatus.pending.value and new_status in {OrderStatus.confirmed, OrderStatus.verified}:
        med_ids = [it.medicine_id for it in order.items]
        med_rows = db.query(Medicine).filter(Medicine.id.in_(med_ids)).all()
        med_map = {m.id: m for m in med_rows}
        for it in order.items:
            med = med_map.get(it.medicine_id)
            if not med:
                raise HTTPException(status_code=400, detail=f"Medicine id {it.medicine_id} not found for stock update")
            units_to_reduce = it.strips_count if (it.strips_count or 0) > 0 else max(it.quantity, 1)
            if (med.stock or 0) < units_to_reduce:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {med.name}. Available {med.stock}, required {units_to_reduce}",
                )
        for it in order.items:
            med = med_map[it.medicine_id]
            units_to_reduce = it.strips_count if (it.strips_count or 0) > 0 else max(it.quantity, 1)
            med.stock = (med.stock or 0) - units_to_reduce

    now = datetime.utcnow()
    order.status = new_status
    order.last_status_updated_by_role = current_user.role
    order.last_status_updated_by_name = current_user.name or current_user.email or f"User #{current_user.id}"
    order.last_status_updated_at = now
    if current_user.role == "pharmacy_store" and new_status == OrderStatus.verified:
        order.pharmacy_approved_by_name = current_user.name or current_user.email or f"User #{current_user.id}"
        order.pharmacy_approved_at = now
    db.commit()
    db.refresh(order)

    if new_status.value != OrderStatus.pending.value:
        order_owner = db.query(User).filter(User.id == order.user_id).first()
        title = "Order Update"
        body = f"{order.order_uid} status is now {new_status.value.upper()}"
        create_notification(db, order.user_id, NotificationType.order, title, body, has_action=True)
        db.commit()
        if order_owner:
            status_snapshot = {
                "order_uid": order.order_uid,
                "status": order.status.value if hasattr(order.status, "value") else str(order.status),
                "payment_method": order.payment_method,
                "total": order.total,
                "pharmacy": order.pharmacy,
                "items": [{"name": it.name, "quantity": it.quantity, "price": it.price} for it in order.items],
            }
            run_in_background(send_push_to_token, order_owner.push_token, title, body, order_owner.id)
            run_in_background(send_order_email_snapshot, order_owner.email, status_snapshot, "RxCompute Order")
    dispatch_webhook(
        db,
        event_type="order_status_updated",
        payload={
            "order_id": order.id,
            "order_uid": order.order_uid,
            "user_id": order.user_id,
            "status": order.status.value,
            "updated_by": current_user.id,
            "updated_by_role": current_user.role,
        },
    )
    return order
