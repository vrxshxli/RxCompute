"""
Order Agent API — Autonomous Order Execution

  POST /order-agent/execute    → Full autonomous pipeline: safety → scheduler → order
  POST /order-agent/place      → Direct order placement (safety pre-approved)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.notification import NotificationType
from models.user import User
from exception_agent.exception_agent import handle_order_exceptions
from order_agent.order_agent import place_order
from saftery_policies_agents.graph import process_with_safety
from schedular_agent.schedular_agent import route_order_to_pharmacy
from services.notifications import create_notification

router = APIRouter(prefix="/order-agent", tags=["Order Agent"])


class OrderItem(BaseModel):
    medicine_id: int
    name: str = ""
    quantity: int = 1
    price: float = 0.0
    dosage_instruction: str | None = None
    strips_count: int = 1
    prescription_file: str | None = None


class ExecuteRequest(BaseModel):
    items: list[OrderItem]
    payment_method: str = ""
    delivery_address: str = ""
    delivery_lat: float | None = None
    delivery_lng: float | None = None
    source: str = "api"


def _publish_agent_trace(
    db: Session,
    *,
    actor: User,
    target_user_id: int,
    agent_name: str,
    phase: str,
    title: str,
    body: str,
    payload: dict | None = None,
) -> None:
    admins = db.query(User).filter(User.role == "admin").all()
    metadata = {
        "agent_name": agent_name,
        "phase": phase,
        "target_user_id": target_user_id,
        "target_user_name": actor.name if actor.id == target_user_id else None,
        "triggered_by_user_id": actor.id,
        "triggered_by_role": actor.role,
        **(payload or {}),
    }
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
    db.commit()


@router.post("/execute")
def execute_full_pipeline(
    data: ExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FULL AUTONOMOUS PIPELINE:
      1. Safety Agent checks all items
      2. Scheduler Agent picks best pharmacy
      3. Order Agent creates order + decrements stock + notifies everyone

    One API call does EVERYTHING. This is what "agentic" means.
    Full Langfuse trace for judges.

    Request:
    {
      "items": [{"medicine_id": 1, "name": "Omega-3", "quantity": 2, "price": 27.0}],
      "payment_method": "UPI",
      "delivery_address": "Mumbai Central"
    }
    """
    if not data.items:
        raise HTTPException(400, "No items")

    items_dicts = [it.model_dump() for it in data.items]
    source = (data.source or "api").strip().lower()
    _publish_agent_trace(
        db,
        actor=current_user,
        target_user_id=current_user.id,
        agent_name="order_agent",
        phase="order_agent_execute_start",
        title="Order Agent Trace",
        body=f"Order agent pipeline started via {source}.",
        payload={"source": source, "item_count": len(items_dicts)},
    )
    if source in {"chat", "conversational", "conversational_agent"}:
        _publish_agent_trace(
            db,
            actor=current_user,
            target_user_id=current_user.id,
            agent_name="conversational_agent",
            phase="conversation_order_intent",
            title="Conversational Agent Trace",
            body="Conversation agent confirmed order intent and delegated to order agent.",
            payload={"source": source, "item_count": len(items_dicts)},
        )

    # STEP 1: Safety check
    safety = process_with_safety(
        user_id=current_user.id,
        matched_medicines=items_dicts,
        user_message="Order Agent autonomous execution",
    )

    if safety.get("has_blocks"):
        exception_result = handle_order_exceptions(
            user_id=current_user.id,
            safety_results=safety.get("safety_results", []) or [],
            matched_medicines=items_dicts,
        )
        _publish_agent_trace(
            db,
            actor=current_user,
            target_user_id=current_user.id,
            agent_name="order_agent",
            phase="order_agent_blocked_by_safety",
            title="Order Agent Trace",
            body="Order agent execution blocked by safety checks.",
            payload={"source": source, "safety_summary": safety.get("safety_summary", "")},
        )
        return {
            "success": False,
            "stage": "safety_agent",
            "blocked": True,
            "safety_summary": safety.get("safety_summary", ""),
            "safety_results": safety.get("safety_results", []),
            "exception_result": exception_result,
        }
    if safety.get("has_warnings"):
        exception_result = handle_order_exceptions(
            user_id=current_user.id,
            safety_results=safety.get("safety_results", []) or [],
            matched_medicines=items_dicts,
        )
        escalation_summary = exception_result.get("escalation_summary", {}) if isinstance(exception_result, dict) else {}
        l2 = int(escalation_summary.get("L2_pharmacist", 0) or 0)
        l3 = int(escalation_summary.get("L3_admin", 0) or 0)
        l4 = int(escalation_summary.get("L4_hard_block", 0) or 0)
        if (l2 + l3 + l4) > 0:
            _publish_agent_trace(
                db,
                actor=current_user,
                target_user_id=current_user.id,
                agent_name="order_agent",
                phase="order_agent_held_by_exception",
                title="Order Agent Trace",
                body="Order agent execution held by exception agent review requirements.",
                payload={"source": source, "exception_result": exception_result},
            )
            return {
                "success": False,
                "stage": "exception_agent",
                "blocked": True,
                "safety_summary": safety.get("safety_summary", ""),
                "safety_results": safety.get("safety_results", []),
                "exception_result": exception_result,
            }

    # STEP 2: Scheduler picks pharmacy
    scheduler = route_order_to_pharmacy(
        user_id=current_user.id,
        order_items=items_dicts,
    )
    pharmacy = scheduler.get("assigned_pharmacy", "")

    # STEP 3: Order Agent executes
    result = place_order(
        user_id=current_user.id,
        items=items_dicts,
        pharmacy=pharmacy,
        payment_method=data.payment_method,
        delivery_address=data.delivery_address,
        delivery_lat=data.delivery_lat,
        delivery_lng=data.delivery_lng,
    )
    _publish_agent_trace(
        db,
        actor=current_user,
        target_user_id=current_user.id,
        agent_name="order_agent",
        phase="order_agent_execute_complete",
        title="Order Agent Trace",
        body=f"Order agent execution completed ({'success' if result.get('success') else 'failed'}).",
        payload={
            "source": source,
            "order_id": result.get("order_id"),
            "order_uid": result.get("order_uid"),
            "success": bool(result.get("success")),
            "error": result.get("error", ""),
        },
    )

    return {
        "success": result.get("success", False),
        "stage": "order_agent",
        "order_uid": result.get("order_uid", ""),
        "order_id": result.get("order_id", 0),
        "total": result.get("total", 0),
        "assigned_pharmacy": pharmacy,
        "routing_reason": scheduler.get("routing_reason", ""),
        "safety_summary": safety.get("safety_summary", ""),
        "has_warnings": safety.get("has_warnings", False),
        "stock_changes": result.get("stock_changes", []),
        "audit_trail": result.get("audit_trail", []),
        "notifications_sent": result.get("notifications_sent", 0),
        "webhook_dispatched": result.get("webhook_dispatched", False),
        "medications_auto_created": result.get("medications_created", 0),
        "execution_time_ms": result.get("execution_time_ms", 0),
        "error": result.get("error", ""),
    }


@router.post("/place")
def place_direct(
    data: ExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Direct order placement — assumes safety already checked.
    Use when safety was pre-checked via /safety/check endpoint.
    """
    if not data.items:
        raise HTTPException(400, "No items")

    items_dicts = [it.model_dump() for it in data.items]

    result = place_order(
        user_id=current_user.id,
        items=items_dicts,
        pharmacy="",  # will be auto-assigned if empty
        payment_method=data.payment_method,
        delivery_address=data.delivery_address,
        delivery_lat=data.delivery_lat,
        delivery_lng=data.delivery_lng,
    )
    _publish_agent_trace(
        db,
        actor=current_user,
        target_user_id=current_user.id,
        agent_name="order_agent",
        phase="order_agent_place_direct",
        title="Order Agent Trace",
        body=f"Direct order agent placement {'succeeded' if result.get('success') else 'failed'}.",
        payload={"order_id": result.get("order_id"), "order_uid": result.get("order_uid"), "error": result.get("error", "")},
    )
    return result