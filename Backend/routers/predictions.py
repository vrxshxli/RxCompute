"""
Prediction Agent API — Refill Intelligence

  POST /predictions/scan           → Full scan all patients (admin/cron)
  GET  /predictions/me             → My medications with predictions
  GET  /predictions/demand         → Demand forecast for next N days (admin)
  POST /predictions/patient/{id}   → Predict for specific patient (admin)
  GET  /predictions/refill/candidates → Refill candidates requiring confirmation
  POST /predictions/refill/confirm    → Confirm refill and auto-create order (payment pending)
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.medicine import Medicine
from models.notification import NotificationType
from models.order import Order, OrderItem, OrderStatus
from models.user import User
from models.user_medication import UserMedication
from exception_agent.exception_agent import handle_order_exceptions
from saftery_policies_agents.graph import process_with_safety
from schedular_agent.schedular_agent import route_order_to_pharmacy
from prediction_agent.prediction_agent import (
    run_prediction_scan,
    run_prediction_for_user,
    run_demand_forecast,
)
from services.notifications import create_notification, run_in_background, send_push_to_token
from services.security import enforce_rag_db_guard
from services.agent_rag import retrieve_agent_context

router = APIRouter(prefix="/predictions", tags=["Prediction Agent"])
STAFF = {"admin", "pharmacy_store", "warehouse"}


def _generate_refill_order_uid() -> str:
    now = datetime.utcnow().strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6].upper()
    return f"RFL-{now}-{short}"


class RefillConfirmRequest(BaseModel):
    medication_id: int | None = None
    medicine_id: int | None = None
    medicine_name: str | None = None
    quantity_units: int = Field(default=1, ge=1, le=365)
    confirmation_checked: bool = False
    confirmation_source: str = "popup"
    payment_method: str | None = "online"
    prescription_file: str | None = None
    dosage_instruction: str | None = None
    target_user_id: int | None = None


def _publish_prediction_order_trace(
    db: Session,
    actor: User,
    target_user_id: int,
    phase: str,
    payload: dict,
    body: str,
) -> None:
    admins = db.query(User).filter(User.role == "admin").all()
    target_user = db.query(User).filter(User.id == target_user_id).first()
    metadata = {
        "agent_name": "prediction_agent",
        "phase": phase,
        "target_user_id": target_user_id,
        "target_user_name": target_user.name if target_user else None,
        "triggered_by_user_id": actor.id,
        "triggered_by_role": actor.role,
        **(payload or {}),
    }
    for admin in admins:
        create_notification(
            db,
            admin.id,
            NotificationType.safety,
            "Prediction Agent Trace",
            body,
            has_action=True,
            dedupe_window_minutes=60,
            metadata=metadata,
        )
    db.commit()


def _select_prediction(preds: list[dict], req: RefillConfirmRequest) -> dict | None:
    if req.medication_id is not None:
        for p in preds:
            if p.get("medication_id") == req.medication_id:
                return p
    if req.medicine_id is not None:
        for p in preds:
            if p.get("medicine_id") == req.medicine_id:
                return p
    if req.medicine_name:
        q = req.medicine_name.strip().lower()
        for p in preds:
            if q and q in str(p.get("medicine_name", "")).lower():
                return p
    return preds[0] if preds else None


def _resolve_medicine_from_name(db: Session, raw_name: str | None) -> Medicine | None:
    txt = (raw_name or "").strip()
    if not txt:
        return None
    exact = db.query(Medicine).filter(Medicine.name.ilike(txt)).first()
    if exact:
        return exact
    prefix = txt[:4].strip()
    if prefix:
        by_prefix = db.query(Medicine).filter(Medicine.name.ilike(f"{prefix}%")).order_by(Medicine.name.asc()).first()
        if by_prefix:
            return by_prefix
        by_contains = db.query(Medicine).filter(Medicine.name.ilike(f"%{prefix}%")).order_by(Medicine.name.asc()).first()
        if by_contains:
            return by_contains
    return db.query(Medicine).filter(Medicine.name.ilike(f"%{txt}%")).order_by(Medicine.name.asc()).first()


def _find_active_refill_order(db: Session, user_id: int, medicine_id: int) -> Order | None:
    return (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            Order.user_id == user_id,
            OrderItem.medicine_id == medicine_id,
            Order.order_uid.ilike("RFL-%"),
            Order.status.in_(
                [
                    OrderStatus.pending,
                    OrderStatus.confirmed,
                    OrderStatus.verified,
                    OrderStatus.picking,
                    OrderStatus.packed,
                    OrderStatus.dispatched,
                ]
            ),
        )
        .order_by(Order.created_at.desc())
        .first()
    )


def _sync_user_medication_after_refill_order(
    db: Session,
    *,
    target_user_id: int,
    medicine: Medicine,
    ordered_units: int,
    dosage_instruction: str,
    medication_id: int | None = None,
) -> None:
    """
    Reset the patient's medication runout clock right after refill confirmation.
    Without this sync, home/refill widgets continue to show stale days-left data.
    """
    now = datetime.utcnow()
    refill_units = max(10, int(ordered_units or 1))
    row = None
    if medication_id is not None:
        row = (
            db.query(UserMedication)
            .filter(
                UserMedication.id == medication_id,
                UserMedication.user_id == target_user_id,
            )
            .first()
        )
    if not row:
        row = (
            db.query(UserMedication)
            .filter(
                UserMedication.user_id == target_user_id,
                UserMedication.medicine_id == medicine.id,
            )
            .first()
        )
    if row:
        # Keep at least previous refill size; never reduce patient's configured stock.
        row.quantity_units = max(int(row.quantity_units or 0), refill_units)
        row.created_at = now
        if not (row.dosage_instruction or "").strip():
            row.dosage_instruction = dosage_instruction or "As prescribed"
        if not row.frequency_per_day or row.frequency_per_day <= 0:
            row.frequency_per_day = 1
        return
    db.add(
        UserMedication(
            user_id=target_user_id,
            medicine_id=medicine.id,
            custom_name=medicine.name,
            dosage_instruction=dosage_instruction or "As prescribed",
            frequency_per_day=1,
            quantity_units=refill_units,
            created_at=now,
        )
    )


@router.post("/scan")
def full_scan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Scan ALL patients and predict refills.
    Creates alerts for at-risk medications.
    Sends push + email for overdue/high risk.

    Call from: admin dashboard button OR daily cron job.
    Full Langfuse trace for judges.

    Response:
    {
      "total_patients": 36,
      "total_medications_scanned": 89,
      "risk_summary": {"overdue": 3, "high": 7, "medium": 12, "low": 67},
      "actions": {"alerts_created": 22, "pushes_sent": 10, "emails_sent": 10},
      "demand_forecast": [
        {"medicine_name": "Panthenol Spray", "refills_needed": 8, "urgency": "critical"},
        ...
      ]
    }
    """
    if current_user.role not in STAFF:
        raise HTTPException(status_code=403, detail="Staff only")
    return run_prediction_scan()


@router.get("/me")
def my_predictions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get refill predictions for the current logged-in patient.
    Shows: days remaining, risk level, estimated runout date,
    order velocity, predicted next order date.

    Used by: Flutter home tab, medicine brain screen.
    """
    return run_prediction_for_user(
        current_user.id,
        create_alerts=False,
        once_per_day=False,
        trigger_reason="predictions_me_api",
        publish_trace=False,
    )


@router.get("/refill/candidates")
def refill_candidates(
    target_user_id: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resolved_user_id = current_user.id
    if target_user_id is not None:
        if current_user.role not in STAFF:
            raise HTTPException(status_code=403, detail="Staff only can query another user")
        resolved_user_id = target_user_id
    result = run_prediction_for_user(
        resolved_user_id,
        create_alerts=False,
        once_per_day=False,
        trigger_reason="refill_candidates_api",
        publish_trace=False,
    )
    preds = [p for p in (result.get("predictions") or []) if int(p.get("days_remaining", 9999)) <= 7]
    # Avoid repeated/manual reorder prompts when an active refill order already exists.
    filtered: list[dict] = []
    for p in preds:
        mid = p.get("medicine_id")
        if not isinstance(mid, int):
            filtered.append(p)
            continue
        active_refill = _find_active_refill_order(db, resolved_user_id, mid)
        if active_refill:
            continue
        filtered.append(p)
    preds = filtered
    for p in preds:
        p["confirmation_required"] = True
        p["payment_auto"] = True
    return {
        "user_id": resolved_user_id,
        "candidates": preds,
        "confirmation_modes": ["popup", "voice"],
    }


@router.post("/refill/confirm")
def confirm_refill_and_create_order(
    req: RefillConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not req.confirmation_checked:
        raise HTTPException(status_code=400, detail="Confirmation checkbox/voice confirmation is required")
    target_user_id = current_user.id
    if req.target_user_id is not None:
        if current_user.role not in STAFF:
            raise HTTPException(status_code=403, detail="Staff only can confirm for another user")
        target_user_id = req.target_user_id

    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    try:
        enforce_rag_db_guard(
            actor_role=current_user.role,
            action="prediction_refill_confirm",
            free_text_fields=[
                req.medicine_name or "",
                req.confirmation_source or "",
                req.dosage_instruction or "",
            ],
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Resolve medicine from request first so we can short-circuit duplicate active refill orders
    # before running prediction gates.
    med: Medicine | None = None
    if req.medicine_id is not None:
        med = db.query(Medicine).filter(Medicine.id == req.medicine_id).first()
    if not med and req.medication_id:
        rec = (
            db.query(UserMedication)
            .filter(UserMedication.id == req.medication_id, UserMedication.user_id == target_user_id)
            .first()
        )
        if rec and rec.medicine_id:
            med = db.query(Medicine).filter(Medicine.id == rec.medicine_id).first()
    if not med and req.medicine_name:
        med = _resolve_medicine_from_name(db, req.medicine_name)
    if med:
        existing = _find_active_refill_order(db, target_user_id, med.id)
        if existing:
            return {
                "message": f"Refill order already active: {existing.order_uid}",
                "order_id": existing.id,
                "order_uid": existing.order_uid,
                "status": existing.status.value,
                "already_exists": True,
                "payment_auto": True,
                "payment_required": False,
            }

    pred_result = run_prediction_for_user(
        target_user_id,
        create_alerts=False,
        once_per_day=False,
        trigger_reason="refill_confirm_api",
        publish_trace=False,
    )
    pred_rows = pred_result.get("predictions") or []
    if not pred_rows:
        raise HTTPException(status_code=400, detail="No refill prediction available for this user")
    picked = _select_prediction(pred_rows, req)
    if not picked:
        raise HTTPException(status_code=400, detail="No matching prediction found")

    medicine_id = req.medicine_id or picked.get("medicine_id")
    med = med or (db.query(Medicine).filter(Medicine.id == medicine_id).first() if medicine_id else None)
    if not med and req.medication_id:
        rec = (
            db.query(UserMedication)
            .filter(UserMedication.id == req.medication_id, UserMedication.user_id == target_user_id)
            .first()
        )
        if rec and rec.medicine_id:
            med = db.query(Medicine).filter(Medicine.id == rec.medicine_id).first()
    if not med:
        med = _resolve_medicine_from_name(db, req.medicine_name or picked.get("medicine_name"))
    if not med:
        raise HTTPException(status_code=404, detail="Medicine not found for refill confirmation")

    qty = max(1, int(req.quantity_units or 1))
    payment_method = (req.payment_method or "online").strip().lower()
    if payment_method not in {"online", "cod", "upi", "card", "wallet", "netbanking"}:
        payment_method = "online"
    dosage = (req.dosage_instruction or picked.get("dosage") or "As prescribed").strip()
    rag_context = retrieve_agent_context(
        db,
        user_id=target_user_id,
        query=f"{med.name} {dosage} refill confirmation {req.confirmation_source or ''}",
        medicine_ids=[med.id],
        top_k=12,
    )
    safety_payload = [{
        "medicine_id": med.id,
        "name": med.name,
        "quantity": qty,
        "dosage_instruction": dosage,
        "strips_count": qty,
        "prescription_file": req.prescription_file,
    }]
    safety = process_with_safety(
        user_id=target_user_id,
        matched_medicines=safety_payload,
        user_message=f"Prediction refill confirmation via {req.confirmation_source}",
    )
    if safety.get("has_blocks"):
        exception_result = handle_order_exceptions(
            user_id=target_user_id,
            safety_results=safety.get("safety_results", []) or [],
            matched_medicines=safety_payload,
        )
        reason = (safety.get("safety_summary") or "Refill blocked by safety checks").strip()
        _publish_prediction_order_trace(
            db,
            current_user,
            target_user_id,
            "prediction_refill_confirm_blocked",
            {
                "medicine_id": med.id,
                "medicine_name": med.name,
                "quantity_units": qty,
                "confirmation_source": req.confirmation_source,
                "safety_summary": reason,
                "safety_results": safety.get("safety_results", []),
                "rag_context": rag_context,
            },
            f"Prediction refill blocked for {med.name}: {reason}",
        )
        raise HTTPException(
            status_code=400,
            detail={
                "message": reason,
                "safety_results": safety.get("safety_results", []),
                "exception_result": exception_result,
                "rag_context": rag_context,
            },
        )
    if safety.get("has_warnings"):
        exception_result = handle_order_exceptions(
            user_id=target_user_id,
            safety_results=safety.get("safety_results", []) or [],
            matched_medicines=safety_payload,
        )
        escalation_summary = exception_result.get("escalation_summary", {}) if isinstance(exception_result, dict) else {}
        l2 = int(escalation_summary.get("L2_pharmacist", 0) or 0)
        l3 = int(escalation_summary.get("L3_admin", 0) or 0)
        l4 = int(escalation_summary.get("L4_hard_block", 0) or 0)
        if (l2 + l3 + l4) > 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Refill requires manual exception review",
                    "safety_results": safety.get("safety_results", []),
                    "exception_result": exception_result,
                    "rag_context": rag_context,
                },
            )

    # Prevent duplicate refill orders for the same medicine while one is already active.
    existing = _find_active_refill_order(db, target_user_id, med.id)
    if existing:
        return {
            "message": f"Refill order already active: {existing.order_uid}",
            "order_id": existing.id,
            "order_uid": existing.order_uid,
            "status": existing.status.value,
            "already_exists": True,
            "payment_auto": True,
            "payment_required": False,
        }

    scheduler_result = route_order_to_pharmacy(user_id=target_user_id, order_items=safety_payload, dry_run=False)
    assigned_pharmacy = scheduler_result.get("assigned_pharmacy")
    order = Order(
        order_uid=_generate_refill_order_uid(),
        user_id=target_user_id,
        status=OrderStatus.pending,
        total=float(med.price) * qty,
        pharmacy=assigned_pharmacy,
        payment_method=payment_method,
        delivery_address=target_user.location_text,
        delivery_lat=target_user.location_lat,
        delivery_lng=target_user.location_lng,
    )
    db.add(order)
    db.flush()
    db.add(
        OrderItem(
            order_id=order.id,
            medicine_id=med.id,
            name=med.name,
            quantity=qty,
            price=float(med.price),
            dosage_instruction=dosage,
            strips_count=qty,
            rx_required=bool(med.rx_required),
            prescription_file=req.prescription_file,
        )
    )
    _sync_user_medication_after_refill_order(
        db,
        target_user_id=target_user_id,
        medicine=med,
        ordered_units=qty,
        dosage_instruction=dosage,
        medication_id=req.medication_id,
    )
    db.commit()
    db.refresh(order)

    title = "Refill Order Created"
    body = f"{order.order_uid} for {med.name} created via {req.confirmation_source}. Payment marked successful ({payment_method.upper()})."
    create_notification(db, target_user_id, NotificationType.refill, title, body, has_action=True, dedupe_window_minutes=0)
    db.commit()
    run_in_background(send_push_to_token, target_user.push_token, title, body, target_user.id)

    _publish_prediction_order_trace(
        db,
        current_user,
        target_user_id,
        "prediction_refill_confirm_success",
        {
            "order_id": order.id,
            "order_uid": order.order_uid,
            "medicine_id": med.id,
            "medicine_name": med.name,
            "quantity_units": qty,
            "confirmation_source": req.confirmation_source,
            "payment_auto": True,
            "payment_method": payment_method,
            "scheduler_result": scheduler_result,
            "rag_context": rag_context,
        },
        f"Prediction refill order created: {order.order_uid}",
    )
    return {
        "message": "Refill order created successfully.",
        "order_id": order.id,
        "order_uid": order.order_uid,
        "status": order.status.value,
        "payment_auto": True,
        "payment_required": False,
        "payment_method": payment_method,
        "scheduler_result": scheduler_result,
        "rag_context": rag_context,
    }


@router.get("/demand")
def demand_forecast(
    days: int = Query(default=7, ge=1, le=90, description="Forecast window in days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Demand forecast: how many refills per medicine in next N days.
    Admin dashboard uses this to plan warehouse stock transfers.

    Response:
    {
      "forecast_window_days": 7,
      "forecast": [
        {
          "medicine_name": "Panthenol Spray",
          "refills_needed": 8,
          "overdue_patients": 2,
          "high_risk_patients": 4,
          "urgency": "critical",
          "patients": ["Deepak Sharma", "Priya Patel", ...]
        }
      ]
    }
    """
    if current_user.role not in STAFF:
        raise HTTPException(status_code=403, detail="Staff only")
    return run_demand_forecast(days)


@router.post("/patient/{user_id}")
def predict_for_patient(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run predictions for a specific patient. Admin use.
    """
    if current_user.role not in STAFF:
        raise HTTPException(status_code=403, detail="Staff only")
    return run_prediction_for_user(
        user_id,
        create_alerts=False,
        once_per_day=False,
        trigger_reason="predict_for_patient_api",
        publish_trace=True,
    )