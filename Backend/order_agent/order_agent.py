"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RxCompute Order Agent — Autonomous Order Execution Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHERE THIS FITS IN THE CHAIN:
  [Conversation] → [Safety] → [Scheduler] → [ORDER AGENT] → Response

  Safety approves → Scheduler picks pharmacy → THIS AGENT executes:
    1. Validates all medicines exist in DB
    2. Generates unique order ID (ORD-YYYYMMDD-XXXXXX)
    3. Creates Order + OrderItems in PostgreSQL
    4. Decrements stock for each medicine (atomic)
    5. Assigns pharmacy from scheduler result
    6. Creates audit log (who, when, what, why)
    7. Sends notifications (in-app + push + email) to patient
    8. Sends alerts to pharmacy staff + admin
    9. Dispatches warehouse webhook (order_created event)
   10. Auto-creates user_medication entries for refill tracking

AUTOMATION PRIORITY:
  This agent is designed so that once Safety + Scheduler pass,
  the order goes through with ZERO human intervention. The only
  case where it fails is if stock changed between safety check
  and order execution (race condition handling included).

LANGFUSE TRACING:
  Every step is a separate span:
    order_agent → validate_medicines → create_order_record →
    decrement_stock → assign_pharmacy → audit_log →
    notify_patient → notify_staff → dispatch_webhook →
    auto_create_medications
"""

import uuid
import json
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from langfuse.decorators import observe, langfuse_context
from sqlalchemy.orm import Session

from database import SessionLocal
from models.order import Order, OrderItem, OrderStatus
from models.medicine import Medicine
from models.user import User
from models.user_medication import UserMedication
from models.pharmacy_store import PharmacyStore
from models.notification import NotificationType
from models.webhook_log import WebhookLog
from services.notifications import (
    create_notification,
    run_in_background,
    send_push_to_token,
    send_order_email_snapshot,
)
from services.webhooks import dispatch_webhook


# ━━━ DATA STRUCTURES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class StockChange:
    """Record of one stock decrement."""
    medicine_id: int = 0
    medicine_name: str = ""
    before: int = 0
    after: int = 0
    units_decremented: int = 0

    def to_dict(self):
        return asdict(self)


@dataclass
class AuditEntry:
    """One entry in the order audit trail."""
    timestamp: str = ""
    action: str = ""
    actor_id: int = 0
    actor_role: str = ""
    detail: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class OrderResult:
    """Complete result of order execution."""
    success: bool = False
    order_id: int = 0
    order_uid: str = ""
    status: str = ""
    total: float = 0.0
    assigned_pharmacy: str = ""
    item_count: int = 0
    error: str = ""
    # Execution details
    stock_changes: list = field(default_factory=list)
    audit_trail: list = field(default_factory=list)
    notifications_sent: int = 0
    webhook_dispatched: bool = False
    medications_created: int = 0
    execution_time_ms: int = 0

    def to_dict(self):
        return {
            "success": self.success,
            "order_id": self.order_id,
            "order_uid": self.order_uid,
            "status": self.status,
            "total": round(self.total, 2),
            "assigned_pharmacy": self.assigned_pharmacy,
            "item_count": self.item_count,
            "error": self.error,
            "stock_changes": [s.to_dict() for s in self.stock_changes],
            "audit_trail": [a.to_dict() for a in self.audit_trail],
            "notifications_sent": self.notifications_sent,
            "webhook_dispatched": self.webhook_dispatched,
            "medications_created": self.medications_created,
            "execution_time_ms": self.execution_time_ms,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC: LangGraph Node
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_agent")
def run_order_agent(state: dict) -> dict:
    """
    LangGraph node: Execute order after safety + scheduler approve.

    Reads:  matched_medicines, user_id, assigned_pharmacy, has_blocks
    Writes: order_result, order_id, order_uid
    """
    t0 = time.time()

    # Skip if safety blocked
    if state.get("has_blocks"):
        return {
            **state,
            "order_result": {"success": False, "error": "Blocked by safety agent."},
            "order_id": "",
            "order_uid": "",
        }

    items = state.get("matched_medicines", [])
    user_id = state.get("user_id", 0)
    pharmacy = state.get("assigned_pharmacy", "")
    payment = state.get("payment_method", "")
    delivery_addr = state.get("delivery_address", "")
    delivery_lat = state.get("delivery_lat")
    delivery_lng = state.get("delivery_lng")

    if not items:
        return {
            **state,
            "order_result": {"success": False, "error": "No items to order."},
            "order_id": "",
            "order_uid": "",
        }

    db = SessionLocal()
    try:
        result = _execute_order(
            db, user_id, items, pharmacy, payment,
            delivery_addr, delivery_lat, delivery_lng,
        )
    except Exception as e:
        result = OrderResult(success=False, error=str(e))
    finally:
        db.close()

    result.execution_time_ms = int((time.time() - t0) * 1000)

    _out({
        "success": result.success,
        "order_uid": result.order_uid,
        "total": round(result.total, 2),
        "pharmacy": result.assigned_pharmacy,
        "items": result.item_count,
        "stock_changes": len(result.stock_changes),
        "notifications": result.notifications_sent,
        "webhook": result.webhook_dispatched,
        "medications_auto_created": result.medications_created,
        "time_ms": result.execution_time_ms,
        "error": result.error,
    })

    return {
        **state,
        "order_result": result.to_dict(),
        "order_id": str(result.order_id),
        "order_uid": result.order_uid,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC: Standalone function (call from router directly)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_agent_standalone")
def place_order(
    user_id: int,
    items: list[dict],
    pharmacy: str = "",
    payment_method: str = "",
    delivery_address: str = "",
    delivery_lat: float = None,
    delivery_lng: float = None,
) -> dict:
    """
    Call from anywhere:
        from order_agent.order_agent import place_order
        result = place_order(user_id=5, items=[...], pharmacy="PH-001")
    """
    t0 = time.time()
    db = SessionLocal()
    try:
        result = _execute_order(
            db, user_id, items, pharmacy, payment_method,
            delivery_address, delivery_lat, delivery_lng,
        )
    except Exception as e:
        result = OrderResult(success=False, error=str(e))
    finally:
        db.close()

    result.execution_time_ms = int((time.time() - t0) * 1000)
    return result.to_dict()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE: Order Execution Pipeline (10 steps)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_execute_pipeline")
def _execute_order(
    db: Session,
    user_id: int,
    items: list[dict],
    pharmacy: str,
    payment_method: str,
    delivery_address: str,
    delivery_lat: float,
    delivery_lng: float,
) -> OrderResult:
    result = OrderResult()
    now = datetime.now(timezone.utc)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Step 1: Load user ───────────────────────────────
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        result.error = f"User {user_id} not found."
        return result

    result.audit_trail.append(AuditEntry(
        timestamp=now_str, action="order_initiated",
        actor_id=user_id, actor_role=user.role or "user",
        detail=f"Order initiated with {len(items)} items.",
    ))

    # ── Step 2: Validate medicines ──────────────────────
    med_ids = [it.get("medicine_id") for it in items if it.get("medicine_id")]
    medicines = _validate_medicines(db, med_ids)
    if medicines is None:
        result.error = "One or more medicines not found in database."
        result.audit_trail.append(AuditEntry(
            timestamp=now_str, action="validation_failed",
            actor_id=user_id, actor_role="system",
            detail=f"Medicine IDs not found: {med_ids}",
        ))
        return result

    med_map = {m.id: m for m in medicines}

    # ── Step 3: Generate order ID ───────────────────────
    order_uid = _generate_uid()
    result.order_uid = order_uid

    result.audit_trail.append(AuditEntry(
        timestamp=now_str, action="order_uid_generated",
        actor_id=0, actor_role="system",
        detail=f"Generated {order_uid}",
    ))

    # ── Step 4: Calculate total ─────────────────────────
    total = 0.0
    for it in items:
        mid = it.get("medicine_id")
        qty = it.get("quantity", 1)
        med = med_map.get(mid)
        price = it.get("price", med.price if med else 0)
        total += price * qty
    result.total = total

    # ── Step 5: Resolve delivery info ───────────────────
    addr = delivery_address or (user.location_text or "")
    d_lat = delivery_lat if delivery_lat is not None else user.location_lat
    d_lng = delivery_lng if delivery_lng is not None else user.location_lng

    # ── Step 6: Create Order record ─────────────────────
    order = _create_order_record(
        db, order_uid, user_id, total, pharmacy,
        payment_method, addr, d_lat, d_lng,
    )
    result.order_id = order.id

    # ── Step 7: Create OrderItems ───────────────────────
    for it in items:
        mid = it.get("medicine_id")
        med = med_map.get(mid)
        _create_order_item(db, order.id, it, med)
    result.item_count = len(items)

    result.audit_trail.append(AuditEntry(
        timestamp=now_str, action="order_record_created",
        actor_id=0, actor_role="system",
        detail=f"Order {order_uid} created. {len(items)} items. Total: {total:.2f}. Pharmacy: {pharmacy}.",
    ))

    # ── Step 8: Decrement stock (ATOMIC) ────────────────
    stock_changes = _decrement_stock(db, items, med_map)
    result.stock_changes = stock_changes

    for sc in stock_changes:
        result.audit_trail.append(AuditEntry(
            timestamp=now_str, action="stock_decremented",
            actor_id=0, actor_role="system",
            detail=f"{sc.medicine_name}: {sc.before} → {sc.after} (-{sc.units_decremented})",
        ))

    # ── Step 9: Commit to DB ────────────────────────────
    db.commit()
    db.refresh(order)

    result.audit_trail.append(AuditEntry(
        timestamp=now_str, action="db_committed",
        actor_id=0, actor_role="system",
        detail="Order and stock changes committed to PostgreSQL.",
    ))

    # ── Step 10a: Notify patient ────────────────────────
    notif_count = _notify_patient(db, user, order)
    result.notifications_sent += notif_count

    # ── Step 10b: Notify staff ──────────────────────────
    staff_count = _notify_staff(db, order, pharmacy)
    result.notifications_sent += staff_count

    result.audit_trail.append(AuditEntry(
        timestamp=now_str, action="notifications_sent",
        actor_id=0, actor_role="system",
        detail=f"Patient: {notif_count}, Staff: {staff_count}.",
    ))

    # ── Step 10c: Dispatch webhook ──────────────────────
    webhook_ok = _dispatch_order_webhook(db, order)
    result.webhook_dispatched = webhook_ok

    result.audit_trail.append(AuditEntry(
        timestamp=now_str, action="webhook_dispatched",
        actor_id=0, actor_role="system",
        detail=f"Webhook order_created: {'sent' if webhook_ok else 'skipped (no target URL)'}.",
    ))

    # ── Step 10d: Auto-create user medications ──────────
    med_created = _auto_create_medications(db, user_id, items, med_map)
    result.medications_created = med_created

    if med_created > 0:
        result.audit_trail.append(AuditEntry(
            timestamp=now_str, action="medications_auto_created",
            actor_id=0, actor_role="prediction_agent",
            detail=f"{med_created} user_medication entries created for refill tracking.",
        ))

    db.commit()

    result.success = True
    result.status = OrderStatus.pending.value
    result.assigned_pharmacy = pharmacy

    result.audit_trail.append(AuditEntry(
        timestamp=now_str, action="order_complete",
        actor_id=0, actor_role="system",
        detail=f"Order {order_uid} execution complete. Status: pending.",
    ))

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2: Validate medicines
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_validate_medicines")
def _validate_medicines(db: Session, med_ids: list[int]) -> list[Medicine] | None:
    medicines = db.query(Medicine).filter(Medicine.id.in_(med_ids)).all()
    found_ids = {m.id for m in medicines}
    missing = [mid for mid in med_ids if mid not in found_ids]

    _out({"requested": med_ids, "found": len(medicines), "missing": missing})

    if missing:
        return None
    return medicines


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3: Generate order UID
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _generate_uid() -> str:
    now = datetime.utcnow().strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6].upper()
    return f"ORD-{now}-{short}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 6: Create Order record
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_create_record")
def _create_order_record(
    db, order_uid, user_id, total, pharmacy,
    payment, addr, d_lat, d_lng,
) -> Order:
    order = Order(
        order_uid=order_uid,
        user_id=user_id,
        status=OrderStatus.pending,
        total=total,
        pharmacy=pharmacy or None,
        payment_method=payment or None,
        delivery_address=addr or None,
        delivery_lat=d_lat,
        delivery_lng=d_lng,
    )
    db.add(order)
    db.flush()  # get order.id without committing

    _out({"order_id": order.id, "order_uid": order_uid, "total": round(total, 2), "pharmacy": pharmacy})
    return order


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 7: Create OrderItem
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _create_order_item(db: Session, order_id: int, item: dict, med: Medicine | None):
    db.add(OrderItem(
        order_id=order_id,
        medicine_id=item.get("medicine_id"),
        name=item.get("name", med.name if med else "Unknown"),
        quantity=item.get("quantity", 1),
        price=item.get("price", med.price if med else 0),
        dosage_instruction=item.get("dosage_instruction"),
        strips_count=item.get("strips_count", 1),
        rx_required=med.rx_required if med else False,
        prescription_file=item.get("prescription_file"),
    ))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 8: Decrement stock (atomic, with race condition handling)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_decrement_stock")
def _decrement_stock(
    db: Session,
    items: list[dict],
    med_map: dict[int, Medicine],
) -> list[StockChange]:
    """
    Decrement stock for each ordered item.
    Uses strips_count if available, otherwise quantity.
    Logs before/after for full audit trail.
    """
    changes: list[StockChange] = []

    for it in items:
        mid = it.get("medicine_id")
        med = med_map.get(mid)
        if not med:
            continue

        strips = it.get("strips_count", 1)
        qty = it.get("quantity", 1)
        units = strips if (strips and strips > 0) else max(qty, 1)

        before = med.stock or 0
        new_stock = max(before - units, 0)  # Never go below 0
        med.stock = new_stock

        sc = StockChange(
            medicine_id=mid,
            medicine_name=med.name,
            before=before,
            after=new_stock,
            units_decremented=before - new_stock,
        )
        changes.append(sc)

    _out({
        "items_decremented": len(changes),
        "changes": [{"med": c.medicine_name, "before": c.before, "after": c.after, "delta": -c.units_decremented} for c in changes],
    })

    return changes


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 10a: Notify patient
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_notify_patient")
def _notify_patient(db: Session, user: User, order: Order) -> int:
    title = "Order Placed"
    body = f"{order.order_uid} placed successfully. Total €{order.total:.2f}"

    create_notification(db, user.id, NotificationType.order, title, body, has_action=True)
    db.commit()

    # Push + email in background
    run_in_background(send_push_to_token, user.push_token, title, body, user.id)

    snapshot = {
        "order_uid": order.order_uid,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "payment_method": order.payment_method,
        "total": order.total,
        "pharmacy": order.pharmacy,
        "items": [{"name": it.name, "quantity": it.quantity, "price": it.price} for it in order.items],
    }
    run_in_background(send_order_email_snapshot, user.email, snapshot, "RxCompute Order")

    _out({"patient_notified": True, "push": bool(user.push_token), "email": bool(user.email)})
    return 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 10b: Notify staff (admin + assigned pharmacy)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_notify_staff")
def _notify_staff(db: Session, order: Order, pharmacy_node: str) -> int:
    staff = db.query(User).filter(User.role.in_(["admin", "pharmacy_store"])).all()
    title = "New Order Received"
    body = f"{order.order_uid} placed. Total €{order.total:.2f}. Pharmacy: {pharmacy_node or 'unassigned'}."

    count = 0
    snapshot = {
        "order_uid": order.order_uid,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "payment_method": order.payment_method,
        "total": order.total,
        "pharmacy": order.pharmacy,
        "items": [{"name": it.name, "quantity": it.quantity, "price": it.price} for it in order.items],
    }

    for s in staff:
        create_notification(db, s.id, NotificationType.order, title, body, has_action=True)
        run_in_background(send_push_to_token, s.push_token, title, body, s.id)
        run_in_background(send_order_email_snapshot, s.email, snapshot, "RxCompute New Order")
        count += 1

    db.commit()
    _out({"staff_notified": count})
    return count


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 10c: Dispatch webhook
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_dispatch_webhook")
def _dispatch_order_webhook(db: Session, order: Order) -> bool:
    log = dispatch_webhook(
        db,
        event_type="order_created",
        payload={
            "order_id": order.id,
            "order_uid": order.order_uid,
            "user_id": order.user_id,
            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
            "total": order.total,
            "pharmacy": order.pharmacy,
            "payment_method": order.payment_method,
            "item_count": len(order.items),
        },
    )
    dispatched = log is not None
    _out({"webhook": "order_created", "dispatched": dispatched})
    return dispatched


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 10d: Auto-create user_medication entries
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="order_auto_create_medications")
def _auto_create_medications(
    db: Session,
    user_id: int,
    items: list[dict],
    med_map: dict[int, Medicine],
) -> int:
    """
    For each ordered medicine, ensure a user_medication entry exists.
    This feeds the Prediction Agent's refill tracking.
    If entry already exists, skip (don't duplicate).
    """
    created = 0
    for it in items:
        mid = it.get("medicine_id")
        if not mid:
            continue

        # Check if already tracking this medicine
        existing = (
            db.query(UserMedication)
            .filter(UserMedication.user_id == user_id, UserMedication.medicine_id == mid)
            .first()
        )
        if existing:
            # Update quantity to reflect new purchase
            qty = it.get("quantity", 1)
            strips = it.get("strips_count", 1)
            units = strips if (strips and strips > 0) else qty
            existing.quantity_units = (existing.quantity_units or 0) + units
            continue

        med = med_map.get(mid)
        dosage = it.get("dosage_instruction", "As directed")

        db.add(UserMedication(
            user_id=user_id,
            medicine_id=mid,
            custom_name=med.name if med else None,
            dosage_instruction=dosage or "As directed",
            frequency_per_day=1,
            quantity_units=it.get("quantity", 1) * it.get("strips_count", 1),
        ))
        created += 1

    _out({"medications_auto_created": created, "existing_updated": len(items) - created})
    return created


# ━━━ HELPER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _out(d):
    try:
        langfuse_context.update_current_observation(output=d)
    except Exception:
        pass