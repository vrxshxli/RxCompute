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
from models.user import User
from order_agent.order_agent import place_order
from saftery_policies_agents.graph import process_with_safety
from schedular_agent.schedular_agent import route_order_to_pharmacy

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

    # STEP 1: Safety check
    safety = process_with_safety(
        user_id=current_user.id,
        matched_medicines=items_dicts,
        user_message="Order Agent autonomous execution",
    )

    if safety.get("has_blocks"):
        return {
            "success": False,
            "stage": "safety_agent",
            "blocked": True,
            "safety_summary": safety.get("safety_summary", ""),
            "safety_results": safety.get("safety_results", []),
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
    return result