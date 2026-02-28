import uuid
from datetime import datetime
from math import atan2, cos, radians, sin, sqrt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.order import Order, OrderItem, OrderStatus
from models.medicine import Medicine
from models.pharmacy_store import PharmacyStore
from models.notification import NotificationType
from schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from saftery_policies_agents.graph import process_with_safety
from services.notifications import (
    create_notification,
    run_in_background,
    send_push_to_token,
    send_order_email_snapshot,
    send_safety_rejection_email,
)
from services.webhooks import dispatch_webhook
from schedular_agent.schedular_agent import route_order_to_pharmacy

router = APIRouter(prefix="/orders", tags=["Orders"])
STAFF_ROLES = {"admin", "pharmacy_store"}
ALERT_ROLES = {"admin", "pharmacy_store", "warehouse"}


def _generate_order_uid() -> str:
    now = datetime.utcnow().strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6].upper()
    return f"ORD-{now}-{short}"


def _resolve_pharmacy_node_for_user(user: User, db: Session) -> str:
    node_id = f"PH-U{user.id:03d}"
    store = db.query(PharmacyStore).filter(PharmacyStore.node_id == node_id).first()
    return store.node_id if store else node_id


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c


def _find_nearby_pharmacy_node(db: Session, user_lat: float | None, user_lng: float | None) -> str | None:
    active = db.query(PharmacyStore).filter(PharmacyStore.active == True).all()
    if not active:
        return None
    if user_lat is None or user_lng is None:
        # No user coords: choose least loaded active store.
        fallback = sorted(active, key=lambda s: (s.load or 0, s.id))[0]
        return fallback.node_id
    with_coords = [s for s in active if s.location_lat is not None and s.location_lng is not None]
    if not with_coords:
        fallback = sorted(active, key=lambda s: (s.load or 0, s.id))[0]
        return fallback.node_id
    nearest = min(
        with_coords,
        key=lambda s: (_haversine_km(user_lat, user_lng, float(s.location_lat), float(s.location_lng)), s.load or 0),
    )
    return nearest.node_id


def _broadcast_safety_alert(db: Session, title: str, body: str, actor: User | None = None) -> None:
    users = db.query(User).filter(User.role.in_(list(ALERT_ROLES))).all()
    for u in users:
        create_notification(db, u.id, NotificationType.safety, title, body, has_action=True, dedupe_window_minutes=1)
        run_in_background(send_push_to_token, u.push_token, title, body, u.id)
    if actor:
        create_notification(db, actor.id, NotificationType.safety, title, body, has_action=True, dedupe_window_minutes=1)
        run_in_background(send_push_to_token, actor.push_token, title, body, actor.id)
    db.commit()


def _build_safety_trace_metadata(order: Order | None, safety: dict, phase: str) -> dict:
    results = safety.get("safety_results", []) or []
    ocr_details = []
    for row in results:
        if not isinstance(row, dict):
            continue
        rule = str(row.get("rule", ""))
        if "prescription_ocr" not in rule:
            continue
        detail = row.get("detail") if isinstance(row.get("detail"), dict) else {}
        ocr_details.append(
            {
                "medicine_id": row.get("medicine_id"),
                "medicine_name": row.get("medicine_name"),
                "rule": rule,
                "status": row.get("status"),
                "reason": row.get("message"),
                "confidence": detail.get("confidence"),
                "indicators": detail.get("indicators"),
            }
        )
    return {
        "agent_name": "safety_agent",
        "phase": phase,
        "order_id": getattr(order, "id", None) if order else None,
        "order_uid": getattr(order, "order_uid", None) if order else None,
        "has_blocks": bool(safety.get("has_blocks")),
        "has_warnings": bool(safety.get("has_warnings")),
        "safety_summary": safety.get("safety_summary"),
        "ocr_details": ocr_details,
        "safety_results": results,
    }


def _build_scheduler_trace_metadata(
    order: Order | None,
    scheduler_result: dict,
    phase: str,
    triggered_by: User | None = None,
) -> dict:
    return {
        "agent_name": "scheduler_agent",
        "phase": phase,
        "order_id": getattr(order, "id", None) if order else None,
        "order_uid": getattr(order, "order_uid", None) if order else None,
        "assigned_pharmacy": scheduler_result.get("assigned_pharmacy"),
        "routing_reason": scheduler_result.get("routing_reason"),
        "fallback_used": bool(scheduler_result.get("fallback_used")),
        "winning_score": scheduler_result.get("winning_score"),
        "order_item_count": scheduler_result.get("order_item_count"),
        "ranking": scheduler_result.get("ranking", []),
        "disqualification_log": scheduler_result.get("disqualification_log", []),
        "evaluations": scheduler_result.get("evaluations", []),
        "target_user_id": getattr(order, "user_id", None) if order else None,
        "triggered_by_user_id": triggered_by.id if triggered_by else None,
        "triggered_by_role": triggered_by.role if triggered_by else None,
    }


def _publish_safety_trace_for_admins(
    db: Session,
    title: str,
    body: str,
    metadata: dict,
) -> None:
    admins = db.query(User).filter(User.role == "admin").all()
    for admin in admins:
        create_notification(
            db,
            admin.id,
            NotificationType.safety,
            title,
            body,
            has_action=True,
            dedupe_window_minutes=0,
            metadata=metadata,
        )


def _publish_scheduler_alert(
    db: Session,
    assigned_node: str | None,
    title: str,
    body: str,
    metadata: dict,
) -> None:
    admins = db.query(User).filter(User.role == "admin").all()
    pharmacy_users = db.query(User).filter(User.role == "pharmacy_store").all()
    for admin in admins:
        create_notification(
            db,
            admin.id,
            NotificationType.safety,
            title,
            body,
            has_action=True,
            dedupe_window_minutes=0,
            metadata=metadata,
        )
    for user in pharmacy_users:
        if assigned_node and _resolve_pharmacy_node_for_user(user, db) != assigned_node:
            continue
        create_notification(
            db,
            user.id,
            NotificationType.safety,
            title,
            body,
            has_action=True,
            dedupe_window_minutes=0,
            metadata=metadata,
        )
        run_in_background(send_push_to_token, user.push_token, title, body, user.id)


def _auto_review_pending_for_pharmacy(db: Session, pharmacy_user: User) -> None:
    pharmacy_node = _resolve_pharmacy_node_for_user(pharmacy_user, db)
    pending_orders = (
        db.query(Order)
        .filter(
            Order.status == OrderStatus.pending,
            or_(Order.pharmacy == pharmacy_node, Order.pharmacy.is_(None)),
        )
        .order_by(Order.created_at.asc())
        .limit(100)
        .all()
    )
    if not pending_orders:
        return
    changed = False
    for order in pending_orders:
        payload = [
            {
                "medicine_id": it.medicine_id,
                "name": it.name,
                "quantity": it.quantity,
                "dosage_instruction": it.dosage_instruction,
                "strips_count": it.strips_count,
                "prescription_file": it.prescription_file,
            }
            for it in order.items
        ]
        safety = process_with_safety(
            user_id=order.user_id,
            matched_medicines=payload,
            user_message="Pharmacy auto-review pending order",
        )
        trace_meta = _build_safety_trace_metadata(order, safety, "pharmacy_auto_review")
        trace_meta["target_user_id"] = order.user_id
        trace_meta["triggered_by_user_id"] = pharmacy_user.id
        trace_meta["triggered_by_role"] = pharmacy_user.role
        _publish_safety_trace_for_admins(
            db,
            "Safety Agent Trace",
            f"Auto review for {order.order_uid}",
            trace_meta,
        )
        reason = (safety.get("safety_summary") or "").strip() or "Rejected by safety agent"
        now = datetime.utcnow()
        order_owner = db.query(User).filter(User.id == order.user_id).first()

        if safety.get("has_blocks"):
            trace_meta = _build_safety_trace_metadata(order, safety, "pharmacy_auto_review")
            order.status = OrderStatus.cancelled
            order.last_status_updated_by_role = pharmacy_user.role
            order.last_status_updated_by_name = pharmacy_user.name or pharmacy_user.email or f"User #{pharmacy_user.id}"
            order.last_status_updated_at = now
            create_notification(
                db,
                order.user_id,
                NotificationType.safety,
                "Safety Agent Rejected Order",
                reason,
                has_action=True,
                metadata=trace_meta,
            )
            if order_owner:
                run_in_background(send_push_to_token, order_owner.push_token, "Safety Agent Rejected Order", reason, order_owner.id)
                run_in_background(send_safety_rejection_email, order_owner.email, order.order_uid, reason)
            changed = True
            continue

        # Auto-approve if no blocking safety issues.
        med_ids = [it.medicine_id for it in order.items]
        med_rows = db.query(Medicine).filter(Medicine.id.in_(med_ids)).all()
        med_map = {m.id: m for m in med_rows}
        stock_ok = True
        stock_reason = ""
        for it in order.items:
            med = med_map.get(it.medicine_id)
            if not med:
                stock_ok = False
                stock_reason = f"Medicine id {it.medicine_id} not found during auto-review"
                break
            units_to_reduce = it.strips_count if (it.strips_count or 0) > 0 else max(it.quantity, 1)
            if (med.stock or 0) < units_to_reduce:
                stock_ok = False
                stock_reason = f"Insufficient stock for {med.name}. Available {med.stock}, required {units_to_reduce}"
                break
        if not stock_ok:
            order.status = OrderStatus.cancelled
            order.last_status_updated_by_role = pharmacy_user.role
            order.last_status_updated_by_name = pharmacy_user.name or pharmacy_user.email or f"User #{pharmacy_user.id}"
            order.last_status_updated_at = now
            create_notification(db, order.user_id, NotificationType.safety, "Order Rejected During Auto Review", stock_reason, has_action=True)
            if order_owner:
                run_in_background(send_push_to_token, order_owner.push_token, "Order Rejected During Auto Review", stock_reason, order_owner.id)
                run_in_background(send_safety_rejection_email, order_owner.email, order.order_uid, stock_reason)
            changed = True
            continue

        for it in order.items:
            med = med_map[it.medicine_id]
            units_to_reduce = it.strips_count if (it.strips_count or 0) > 0 else max(it.quantity, 1)
            med.stock = (med.stock or 0) - units_to_reduce

        order.status = OrderStatus.verified
        order.last_status_updated_by_role = pharmacy_user.role
        order.last_status_updated_by_name = pharmacy_user.name or pharmacy_user.email or f"User #{pharmacy_user.id}"
        order.last_status_updated_at = now
        order.pharmacy_approved_by_name = pharmacy_user.name or pharmacy_user.email or f"User #{pharmacy_user.id}"
        order.pharmacy_approved_at = now
        if not order.pharmacy or str(order.pharmacy).strip().lower() in {"none", "null", "-"}:
            node_id = f"PH-U{pharmacy_user.id:03d}"
            store = db.query(PharmacyStore).filter(PharmacyStore.node_id == node_id).first()
            order.pharmacy = store.node_id if store else node_id
        create_notification(
            db,
            order.user_id,
            NotificationType.order,
            "Order Auto Approved",
            f"{order.order_uid} verified by pharmacy safety agent.",
            has_action=True,
        )
        if order_owner:
            run_in_background(send_push_to_token, order_owner.push_token, "Order Auto Approved", f"{order.order_uid} verified by pharmacy.", order_owner.id)
        changed = True
    if changed:
        db.commit()


@router.get("/", response_model=list[OrderOut])
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all orders for the current user."""
    if current_user.role == "warehouse":
        raise HTTPException(status_code=403, detail="Warehouse does not have access to customer orders")
    if current_user.role == "pharmacy_store":
        _auto_review_pending_for_pharmacy(db, current_user)
        pharmacy_node = _resolve_pharmacy_node_for_user(current_user, db)
        return (
            db.query(Order)
            .filter(or_(Order.pharmacy == pharmacy_node, Order.pharmacy.is_(None)))
            .order_by(Order.created_at.desc())
            .all()
        )
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
    if current_user.role == "pharmacy_store":
        pharmacy_node = _resolve_pharmacy_node_for_user(current_user, db)
        query = query.filter(or_(Order.pharmacy == pharmacy_node, Order.pharmacy.is_(None)))
    elif current_user.role not in STAFF_ROLES:
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
    safety_payload = [
        {
            "medicine_id": it.medicine_id,
            "name": it.name,
            "quantity": it.quantity,
            "dosage_instruction": it.dosage_instruction,
            "strips_count": it.strips_count,
            "prescription_file": it.prescription_file,
        }
        for it in data.items
    ]
    safety = process_with_safety(
        user_id=current_user.id,
        matched_medicines=safety_payload,
        user_message="Order safety check before create_order",
    )
    trace_meta = _build_safety_trace_metadata(None, safety, "order_create")
    trace_meta["target_user_id"] = current_user.id
    trace_meta["triggered_by_user_id"] = current_user.id
    trace_meta["triggered_by_role"] = current_user.role
    _publish_safety_trace_for_admins(
        db,
        "Safety Agent Trace",
        "User order safety check executed",
        trace_meta,
    )
    safety_summary = (safety.get("safety_summary") or "").strip()
    if safety.get("has_blocks"):
        title = "Safety Alert: Order Blocked"
        body = safety_summary or "Order blocked by safety policy checks."
        _broadcast_safety_alert(db, title, body, current_user)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Order blocked by safety policy",
                "safety_summary": body,
                "safety_results": safety.get("safety_results", []),
            },
        )
    if safety.get("has_warnings"):
        title = "Safety Warning: Review Needed"
        body = safety_summary or "Order has safety warnings. Pharmacist review recommended."
        _broadcast_safety_alert(db, title, body, current_user)
        db.commit()

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
    delivery_address = (data.delivery_address or current_user.location_text or "").strip() or None
    delivery_lat = data.delivery_lat if data.delivery_lat is not None else current_user.location_lat
    delivery_lng = data.delivery_lng if data.delivery_lng is not None else current_user.location_lng
    assigned_pharmacy = data.pharmacy
    scheduler_result = {}
    if not assigned_pharmacy:
        scheduler_result = route_order_to_pharmacy(
            user_id=current_user.id,
            order_items=safety_payload,
            dry_run=False,
        )
        assigned_pharmacy = scheduler_result.get("assigned_pharmacy") or _find_nearby_pharmacy_node(db, delivery_lat, delivery_lng)
    order = Order(
        order_uid=_generate_order_uid(),
        user_id=current_user.id,
        status=OrderStatus.pending,
        total=total,
        pharmacy=assigned_pharmacy,
        payment_method=data.payment_method,
        delivery_address=delivery_address,
        delivery_lat=delivery_lat,
        delivery_lng=delivery_lng,
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
    if scheduler_result:
        scheduler_meta = _build_scheduler_trace_metadata(order, scheduler_result, "order_scheduler_assign", current_user)
        _publish_scheduler_alert(
            db,
            assigned_pharmacy,
            "Scheduler Agent Decision",
            scheduler_result.get("routing_reason", f"{order.order_uid} routed to {assigned_pharmacy}"),
            scheduler_meta,
        )
        db.commit()
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
    auto_reject_reason = ""

    # Pharmacy must approve first. Admin handles downstream logistics.
    if current_user.role == "pharmacy_store":
        pharmacy_node = _resolve_pharmacy_node_for_user(current_user, db)
        if old_status != OrderStatus.pending.value:
            raise HTTPException(status_code=403, detail="Pharmacy can approve only pending orders")
        if new_status not in {OrderStatus.verified, OrderStatus.cancelled}:
            raise HTTPException(status_code=403, detail="Pharmacy can set only VERIFIED or CANCELLED")
        if order.pharmacy and order.pharmacy != pharmacy_node:
            raise HTTPException(status_code=403, detail=f"Order is assigned to pharmacy {order.pharmacy}")
        if not order.pharmacy:
            order.pharmacy = _find_nearby_pharmacy_node(db, order.delivery_lat, order.delivery_lng) or pharmacy_node
        if order.pharmacy != pharmacy_node and new_status == OrderStatus.verified:
            raise HTTPException(status_code=403, detail=f"Nearest assigned pharmacy is {order.pharmacy}")
        if new_status == OrderStatus.verified:
            # Pharmacy verification must pass safety checks, including prescription quality.
            verify_payload = [
                {
                    "medicine_id": it.medicine_id,
                    "name": it.name,
                    "quantity": it.quantity,
                    "dosage_instruction": it.dosage_instruction,
                    "strips_count": it.strips_count,
                    "prescription_file": it.prescription_file,
                }
                for it in order.items
            ]
            safety_verify = process_with_safety(
                user_id=order.user_id,
                matched_medicines=verify_payload,
                user_message="Pharmacy verification safety check",
            )
            verify_trace_meta = _build_safety_trace_metadata(order, safety_verify, "pharmacy_manual_verify")
            verify_trace_meta["target_user_id"] = order.user_id
            verify_trace_meta["triggered_by_user_id"] = current_user.id
            verify_trace_meta["triggered_by_role"] = current_user.role
            _publish_safety_trace_for_admins(
                db,
                "Safety Agent Trace",
                f"Manual verify for {order.order_uid}",
                verify_trace_meta,
            )
            if safety_verify.get("has_blocks"):
                auto_reject_reason = safety_verify.get("safety_summary", "") or "Rejected by safety agent checks"
                new_status = OrderStatus.cancelled
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
        # Ensure assigned pharmacy is always visible after pharmacy verification.
        if not order.pharmacy or str(order.pharmacy).strip().lower() in {"none", "null", "-"}:
            node_id = f"PH-U{current_user.id:03d}"
            store = db.query(PharmacyStore).filter(PharmacyStore.node_id == node_id).first()
            order.pharmacy = store.node_id if store else node_id
    db.commit()
    db.refresh(order)

    if new_status.value != OrderStatus.pending.value:
        order_owner = db.query(User).filter(User.id == order.user_id).first()
        title = "Order Update"
        body = f"{order.order_uid} status is now {new_status.value.upper()}"
        create_notification(db, order.user_id, NotificationType.order, title, body, has_action=True)
        if auto_reject_reason:
            create_notification(
                db,
                order.user_id,
                NotificationType.safety,
                "Safety Agent Rejected Order",
                auto_reject_reason,
                has_action=True,
                dedupe_window_minutes=1,
                metadata=verify_trace_meta if "verify_trace_meta" in locals() else None,
            )
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
            if auto_reject_reason:
                run_in_background(send_push_to_token, order_owner.push_token, "Safety Agent Rejected Order", auto_reject_reason, order_owner.id)
                run_in_background(send_safety_rejection_email, order_owner.email, order.order_uid, auto_reject_reason)
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
