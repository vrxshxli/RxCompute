"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RxCompute Exception Agent — Escalation & Edge Case Handler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHEN SAFETY AGENT BLOCKS AN ORDER, THIS AGENT DECIDES WHAT HAPPENS NEXT.

Safety Agent says "BLOCKED". Exception Agent says "HERE'S WHAT TO DO ABOUT IT."

  Safety blocks → Exception Agent classifies the exception → decides action:

  EXCEPTION TYPE           │ AUTO ACTION
  ─────────────────────────┼──────────────────────────────────────────────────
  Prescription Missing     │ Request upload, hold order, notify patient
  Prescription Invalid     │ Escalate to pharmacist for manual review
  Controlled Substance     │ Require pharmacist + admin dual approval
  Allergy Conflict         │ HARD BLOCK + urgent alert to patient + staff
  Stock Exhausted          │ Auto-search alternatives, suggest substitutes
  High Quantity Suspicious │ Flag for pharmacist review, hold order
  Partial Stock Available  │ Offer partial fulfillment or waitlist
  Unknown Medicine         │ Escalate to admin, log for catalog update

ESCALATION LEVELS:
  L1 — SELF-SERVICE: Patient can resolve (upload prescription, reduce qty)
  L2 — PHARMACIST: Needs pharmacist review + approval
  L3 — ADMIN: Needs admin intervention (controlled substances, catalog)
  L4 — HARD BLOCK: Cannot proceed under any circumstance (allergy conflict)

AUTOMATION PRIORITY:
  For L1 exceptions, the agent TELLS the patient exactly what to do.
  For L2/L3, it auto-creates escalation tickets and notifies the right people.
  For L4, it blocks AND records the reason in the audit trail.
"""

import time
import json
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from langfuse.decorators import observe, langfuse_context
from sqlalchemy.orm import Session

from database import SessionLocal
from models.user import User
from models.medicine import Medicine
from models.order import Order, OrderItem, OrderStatus
from models.notification import NotificationType
from services.notifications import (
    create_notification,
    run_in_background,
    send_push_to_token,
    send_safety_rejection_email,
)
from services.agent_rag import retrieve_agent_context
from services.webhooks import dispatch_webhook


# ━━━ KNOWN CONTROLLED SUBSTANCE KEYWORDS ━━━━━━━━━━━━
# In production: read from DB table. For hackathon: hardcoded list.
CONTROLLED_KEYWORDS = {
    "morphine", "codeine", "tramadol", "oxycodone", "fentanyl",
    "diazepam", "alprazolam", "lorazepam", "zolpidem",
    "methylphenidate", "amphetamine", "modafinil",
    "pregabalin", "gabapentin", "ketamine",
}

# Allergy-medicine conflict map (production: read from drug interaction DB)
ALLERGY_CONFLICTS = {
    "penicillin": ["amoxicillin", "ampicillin", "penicillin", "augmentin"],
    "sulfa": ["sulfamethoxazole", "sulfasalazine", "sulfonamide"],
    "nsaid": ["ibuprofen", "aspirin", "naproxen", "diclofenac"],
    "latex": [],  # no direct medicine conflict but flag for staff
}

HIGH_QTY_THRESHOLD = 5
PARTIAL_FILL_MIN_PERCENT = 0.5  # Offer partial if >= 50% available


# ━━━ DATA STRUCTURES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class ExceptionCase:
    """One exception for one medicine."""
    medicine_id: int = 0
    medicine_name: str = ""
    exception_type: str = ""      # prescription_missing, controlled_substance, allergy_conflict, etc.
    escalation_level: str = ""    # L1, L2, L3, L4
    severity: str = ""            # low, medium, high, critical
    auto_action: str = ""         # What the system did automatically
    patient_action: str = ""      # What the patient needs to do
    staff_action: str = ""        # What staff needs to do (if escalated)
    resolved: bool = False
    resolution: str = ""
    reasoning: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ExceptionResult:
    """Complete exception handling result."""
    total_exceptions: int = 0
    l1_count: int = 0  # self-service
    l2_count: int = 0  # pharmacist
    l3_count: int = 0  # admin
    l4_count: int = 0  # hard block
    auto_resolved: int = 0
    escalated: int = 0
    alternatives_found: int = 0
    notifications_sent: int = 0
    execution_time_ms: int = 0
    exceptions: list = field(default_factory=list)
    alternatives: list = field(default_factory=list)
    patient_instructions: list = field(default_factory=list)
    audit_trail: list = field(default_factory=list)

    def to_dict(self):
        return {
            "total_exceptions": self.total_exceptions,
            "escalation_summary": {
                "L1_self_service": self.l1_count,
                "L2_pharmacist": self.l2_count,
                "L3_admin": self.l3_count,
                "L4_hard_block": self.l4_count,
            },
            "auto_resolved": self.auto_resolved,
            "escalated": self.escalated,
            "alternatives_found": self.alternatives_found,
            "notifications_sent": self.notifications_sent,
            "execution_time_ms": self.execution_time_ms,
            "exceptions": [e.to_dict() for e in self.exceptions],
            "alternatives": self.alternatives,
            "patient_instructions": self.patient_instructions,
            "audit_trail": self.audit_trail,
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC: LangGraph Node
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="exception_agent")
def run_exception_agent(state: dict) -> dict:
    """
    LangGraph node: Handle exceptions from Safety Agent blocks/warnings.

    Reads:  safety_results, matched_medicines, user_id
    Writes: exception_result, patient_instructions
    """
    t0 = time.time()

    safety_results = state.get("safety_results", [])
    items = state.get("matched_medicines", [])
    user_id = state.get("user_id", 0)
    has_blocks = state.get("has_blocks", False)
    has_warnings = state.get("has_warnings", False)

    # Nothing to handle if no blocks/warnings
    if not has_blocks and not has_warnings:
        return {
            **state,
            "exception_result": {"total_exceptions": 0, "message": "No exceptions — all clear."},
            "patient_instructions": [],
        }

    db = SessionLocal()
    try:
        result = _handle_exceptions(db, user_id, safety_results, items)
    finally:
        db.close()

    result.execution_time_ms = int((time.time() - t0) * 1000)

    _out({
        "exceptions": result.total_exceptions,
        "L1": result.l1_count, "L2": result.l2_count,
        "L3": result.l3_count, "L4": result.l4_count,
        "auto_resolved": result.auto_resolved,
        "escalated": result.escalated,
        "alternatives": result.alternatives_found,
        "time_ms": result.execution_time_ms,
    })

    return {
        **state,
        "exception_result": result.to_dict(),
        "patient_instructions": result.patient_instructions,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC: Standalone
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="exception_agent_standalone")
def handle_order_exceptions(
    user_id: int,
    safety_results: list[dict],
    matched_medicines: list[dict],
) -> dict:
    """
    Call from anywhere:
        from exception_agent.exception_agent import handle_order_exceptions
        result = handle_order_exceptions(user_id=5, safety_results=[...], matched_medicines=[...])
    """
    db = SessionLocal()
    try:
        result = _handle_exceptions(db, user_id, safety_results, matched_medicines)
    finally:
        db.close()
    return result.to_dict()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE: Exception Handler Pipeline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="exception_handle_all")
def _handle_exceptions(
    db: Session,
    user_id: int,
    safety_results: list[dict],
    items: list[dict],
) -> ExceptionResult:
    result = ExceptionResult()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    user = db.query(User).filter(User.id == user_id).first()
    user_allergies = _parse_allergies(user) if user else []
    medicine_ids = [int(it.get("medicine_id")) for it in items if isinstance(it, dict) and isinstance(it.get("medicine_id"), int)]
    query = " ".join(
        [
            f"{str(sr.get('medicine_name', ''))} {str(sr.get('rule', ''))} {str(sr.get('message', ''))}"
            for sr in safety_results
            if isinstance(sr, dict)
        ]
    )
    rag_context = retrieve_agent_context(
        db,
        user_id=user_id if user else None,
        query=query or "exception classification",
        medicine_ids=medicine_ids,
        top_k=12,
    )

    # Build items lookup
    items_map = {it.get("medicine_id"): it for it in items}

    for sr in safety_results:
        if not isinstance(sr, dict):
            continue
        status = sr.get("status", "")
        if status == "approved":
            continue

        rule = sr.get("rule", "")
        mid = sr.get("medicine_id", 0)
        mname = sr.get("medicine_name", "")
        item = items_map.get(mid, {})

        exc = _classify_exception(db, user, user_allergies, sr, item)
        result.exceptions.append(exc)
        result.total_exceptions += 1

        # Count by level
        if exc.escalation_level == "L1":
            result.l1_count += 1
        elif exc.escalation_level == "L2":
            result.l2_count += 1
        elif exc.escalation_level == "L3":
            result.l3_count += 1
        elif exc.escalation_level == "L4":
            result.l4_count += 1

        # Patient instructions
        if exc.patient_action:
            result.patient_instructions.append({
                "medicine": mname,
                "instruction": exc.patient_action,
                "severity": exc.severity,
                "escalation": exc.escalation_level,
            })

        # Auto-resolve L1 where possible
        if exc.escalation_level == "L1" and exc.resolved:
            result.auto_resolved += 1

        # Escalate L2/L3/L4
        if exc.escalation_level in ("L2", "L3", "L4"):
            _escalate(db, user, exc, rag_context=rag_context)
            result.escalated += 1
            result.notifications_sent += 1
        _publish_exception_trace(db, user, exc, rag_context)

        # Search alternatives for stock issues
        if rule in ("out_of_stock", "insufficient_stock"):
            alts = _find_alternatives(db, mid, mname)
            if alts:
                result.alternatives.extend(alts)
                result.alternatives_found += len(alts)

        result.audit_trail.append({
            "timestamp": now,
            "medicine": mname,
            "exception": exc.exception_type,
            "level": exc.escalation_level,
            "severity": exc.severity,
            "auto_action": exc.auto_action,
            "resolved": exc.resolved,
            "rag_context": {
                "total_candidates": rag_context.get("total_candidates", 0),
                "snippet_count": len(rag_context.get("snippets", []) or []),
            },
        })

    db.commit()
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLASSIFY: Determine exception type + escalation level
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="exception_classify")
def _classify_exception(
    db: Session,
    user: User | None,
    user_allergies: list[str],
    safety_result: dict,
    item: dict,
) -> ExceptionCase:
    rule = safety_result.get("rule", "")
    mid = safety_result.get("medicine_id", 0)
    mname = safety_result.get("medicine_name", "")
    msg = safety_result.get("message", "")
    qty = item.get("quantity", 1)
    rx_file = item.get("prescription_file")

    exc = ExceptionCase(medicine_id=mid, medicine_name=mname)

    # ── PRESCRIPTION MISSING ────────────────────────────
    if rule == "prescription_required":
        if rx_file:
            # Has file but safety still blocked → invalid/unreadable prescription
            exc.exception_type = "prescription_invalid"
            exc.escalation_level = "L2"
            exc.severity = "high"
            exc.auto_action = "Escalated to pharmacist for manual prescription review."
            exc.patient_action = f"Your prescription for {mname} needs pharmacist verification. Please wait for review."
            exc.staff_action = f"Review uploaded prescription for {mname}. Verify authenticity and approve or reject."
            exc.reasoning = f"Prescription file present ({rx_file}) but safety agent still flagged. Likely OCR check failed or file unreadable."
        else:
            exc.exception_type = "prescription_missing"
            exc.escalation_level = "L1"
            exc.severity = "medium"
            exc.auto_action = "Requested prescription upload from patient."
            exc.patient_action = f"Please upload a valid prescription for {mname}. Tap 'Upload Prescription' in chat to proceed."
            exc.staff_action = ""
            exc.resolved = False  # patient needs to act
            exc.reasoning = f"{mname} has rx_required=True. No prescription_file uploaded."

        # Check if it's a controlled substance too
        if _is_controlled(mname):
            exc.exception_type = "controlled_substance"
            exc.escalation_level = "L3"
            exc.severity = "critical"
            exc.auto_action = "Flagged as controlled substance. Requires pharmacist + admin dual approval."
            exc.patient_action = f"{mname} is a controlled substance. Your order requires pharmacist and admin approval. You will be notified once reviewed."
            exc.staff_action = f"CONTROLLED SUBSTANCE: {mname}. Verify prescription authenticity. Both pharmacist AND admin must approve."

        _out({"type": exc.exception_type, "level": exc.escalation_level, "medicine": mname})
        return exc

    # ── OUT OF STOCK ────────────────────────────────────
    if rule == "out_of_stock":
        exc.exception_type = "stock_exhausted"
        exc.escalation_level = "L1"
        exc.severity = "medium"
        exc.auto_action = "Searching for alternative medicines with similar composition."
        exc.patient_action = f"{mname} is currently out of stock. We're searching for alternatives. You can also check back later."
        exc.staff_action = ""
        exc.reasoning = f"Stock = 0 for {mname}."
        _out({"type": "stock_exhausted", "level": "L1", "medicine": mname})
        return exc

    # ── INSUFFICIENT STOCK ──────────────────────────────
    if rule == "insufficient_stock":
        med = db.query(Medicine).filter(Medicine.id == mid).first()
        available = med.stock if med else 0

        if available >= qty * PARTIAL_FILL_MIN_PERCENT:
            exc.exception_type = "partial_stock_available"
            exc.escalation_level = "L1"
            exc.severity = "low"
            exc.auto_action = f"Partial fulfillment available: {available} of {qty} requested."
            exc.patient_action = f"Only {available} units of {mname} available (you requested {qty}). Would you like to order {available} instead?"
            exc.reasoning = f"Stock {available} >= 50% of requested {qty}. Partial fill offered."
        else:
            exc.exception_type = "stock_exhausted"
            exc.escalation_level = "L1"
            exc.severity = "medium"
            exc.auto_action = "Stock too low for partial fill. Searching alternatives."
            exc.patient_action = f"Only {available} units of {mname} available (you need {qty}). We're searching for alternatives."
            exc.reasoning = f"Stock {available} < 50% of requested {qty}. Cannot partial fill."

        _out({"type": exc.exception_type, "level": exc.escalation_level, "available": available, "requested": qty})
        return exc

    # ── HIGH QUANTITY ───────────────────────────────────
    if rule == "high_quantity":
        if _is_controlled(mname):
            exc.exception_type = "controlled_high_quantity"
            exc.escalation_level = "L3"
            exc.severity = "critical"
            exc.auto_action = "Controlled substance + high quantity flagged. Admin + pharmacist review required."
            exc.patient_action = f"Your order of {qty} units of {mname} (controlled substance) requires admin review."
            exc.staff_action = f"ALERT: {qty} units of controlled substance {mname}. Verify medical necessity."
        else:
            exc.exception_type = "high_quantity_suspicious"
            exc.escalation_level = "L2"
            exc.severity = "medium"
            exc.auto_action = "Flagged for pharmacist review. Order held pending approval."
            exc.patient_action = f"Your order of {qty} units of {mname} exceeds the usual limit. A pharmacist will review it shortly."
            exc.staff_action = f"Review: Patient ordered {qty} units of {mname} (threshold: {HIGH_QTY_THRESHOLD}). Check medical justification."

        exc.reasoning = f"Quantity {qty} > threshold {HIGH_QTY_THRESHOLD}. Controlled: {_is_controlled(mname)}."
        _out({"type": exc.exception_type, "level": exc.escalation_level, "qty": qty})
        return exc

    # ── DUPLICATE ACTIVE MEDICATION ─────────────────────
    if rule == "duplicate_active_medication":
        days_remaining = None
        if isinstance(safety_result.get("detail"), dict):
            days_remaining = safety_result.get("detail", {}).get("days_remaining")
        exc.exception_type = "duplicate_active_medication"
        exc.escalation_level = "L1"
        exc.severity = "medium"
        exc.auto_action = "Blocked duplicate order while existing course is still active."
        if isinstance(days_remaining, int) and days_remaining > 0:
            exc.patient_action = (
                f"You already have active stock for {mname} for about {days_remaining} day(s). "
                "Please wait until current course finishes."
            )
            exc.reasoning = f"Duplicate order blocked with active days remaining={days_remaining}."
        else:
            exc.patient_action = f"You already have active stock for {mname}. Please wait before placing the same order again."
            exc.reasoning = "Duplicate order blocked due to active medication cycle."
        exc.staff_action = ""
        _out({"type": exc.exception_type, "level": exc.escalation_level, "medicine": mname})
        return exc

    # ── MEDICINE NOT FOUND ──────────────────────────────
    if rule in ("medicine_not_found", "not_found"):
        exc.exception_type = "unknown_medicine"
        exc.escalation_level = "L3"
        exc.severity = "medium"
        exc.auto_action = "Escalated to admin for catalog review."
        exc.patient_action = f"We couldn't find '{mname}' in our catalog. Our team has been notified and will add it if available."
        exc.staff_action = f"Medicine '{mname}' (ID: {mid}) not in catalog. Verify and add to database if legitimate."
        exc.reasoning = f"Medicine ID {mid} not found in medicines table."
        _out({"type": "unknown_medicine", "level": "L3", "medicine": mname})
        return exc

    # ── ALLERGY CONFLICT CHECK (runs for ALL exceptions) ─
    if user_allergies:
        conflict = _check_allergy_conflict(mname, user_allergies)
        if conflict:
            exc.exception_type = "allergy_conflict"
            exc.escalation_level = "L4"
            exc.severity = "critical"
            exc.auto_action = f"HARD BLOCK: Patient has allergy to '{conflict['allergy']}'. {mname} may contain conflicting compound."
            exc.patient_action = f"SAFETY ALERT: {mname} may conflict with your reported allergy to '{conflict['allergy']}'. This order CANNOT proceed. Please consult your doctor."
            exc.staff_action = f"ALLERGY CONFLICT: Patient allergic to '{conflict['allergy']}'. Ordered {mname}. BLOCKED automatically."
            exc.reasoning = f"User allergies: {user_allergies}. Medicine '{mname}' matches conflict list for '{conflict['allergy']}'."
            _out({"type": "allergy_conflict", "level": "L4", "allergy": conflict["allergy"], "medicine": mname})
            return exc

    # ── DEFAULT: Unknown rule ───────────────────────────
    exc.exception_type = "unknown_exception"
    exc.escalation_level = "L2"
    exc.severity = "medium"
    exc.auto_action = "Escalated to pharmacist for manual review."
    exc.patient_action = f"Your order for {mname} needs review. A pharmacist will look at it shortly."
    exc.staff_action = f"Review exception for {mname}. Safety rule: {rule}. Message: {msg}"
    exc.reasoning = f"Unrecognized safety rule: {rule}. Defaulting to L2 pharmacist escalation."

    _out({"type": "unknown", "level": "L2", "rule": rule})
    return exc


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ESCALATE: Notify the right people
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="exception_escalate")
def _escalate(db: Session, user: User | None, exc: ExceptionCase, rag_context: dict | None = None):
    """Send notifications to staff based on escalation level."""

    if exc.escalation_level == "L2":
        # Pharmacist review
        targets = db.query(User).filter(User.role == "pharmacy_store").all()
        title = f"Exception Agent: Pharmacist Review: {exc.medicine_name}"
        body = exc.staff_action
        notif_type = NotificationType.safety

    elif exc.escalation_level == "L3":
        # Admin + pharmacist
        targets = db.query(User).filter(User.role.in_(["admin", "pharmacy_store"])).all()
        title = f"Exception Agent: ESCALATION: {exc.medicine_name}"
        body = exc.staff_action
        notif_type = NotificationType.safety

    elif exc.escalation_level == "L4":
        # Everyone — critical safety
        targets = db.query(User).filter(User.role.in_(["admin", "pharmacy_store", "warehouse"])).all()
        title = f"Exception Agent: CRITICAL SAFETY: {exc.medicine_name}"
        body = exc.staff_action
        notif_type = NotificationType.safety
    else:
        return

    for staff in targets:
        create_notification(
            db, staff.id, notif_type, title, body,
            has_action=True, dedupe_window_minutes=30,
            metadata={
                "agent_name": "exception_agent",
                "phase": "exception_escalate",
                "exception_type": exc.exception_type,
                "escalation_level": exc.escalation_level,
                "severity": exc.severity,
                "medicine_id": exc.medicine_id,
                "medicine_name": exc.medicine_name,
                "reasoning": exc.reasoning,
                "target_user_id": user.id if user else None,
                "target_user_name": user.name if user else None,
                "target_user_email": user.email if user else None,
                "target_user_role": user.role if user else None,
                "rag_context": rag_context or {},
            },
        )
        run_in_background(send_push_to_token, staff.push_token, title, body, staff.id)

    # Admin trace for every escalation level so observability is complete.
    admins = db.query(User).filter(User.role == "admin").all()
    trace_title = "Exception Agent Trace"
    trace_body = f"{exc.exception_type} classified as {exc.escalation_level} for {exc.medicine_name}"
    for admin in admins:
        create_notification(
            db,
            admin.id,
            NotificationType.safety,
            trace_title,
            trace_body,
            has_action=True,
            dedupe_window_minutes=0,
            metadata={
                "agent_name": "exception_agent",
                "phase": "exception_trace",
                "exception_type": exc.exception_type,
                "escalation_level": exc.escalation_level,
                "severity": exc.severity,
                "medicine_id": exc.medicine_id,
                "medicine_name": exc.medicine_name,
                "reasoning": exc.reasoning,
                "target_user_id": user.id if user else None,
                "target_user_name": user.name if user else None,
                "target_user_email": user.email if user else None,
                "target_user_role": user.role if user else None,
                "rag_context": rag_context or {},
            },
        )

    # Also notify patient
    if user and exc.patient_action:
        create_notification(
            db, user.id, NotificationType.safety,
            f"Exception Agent Alert: {exc.medicine_name}",
            exc.patient_action,
            has_action=True, dedupe_window_minutes=30,
            metadata={
                "agent_name": "exception_agent",
                "phase": "patient_alert",
                "exception_type": exc.exception_type,
                "escalation_level": exc.escalation_level,
                "severity": exc.severity,
                "medicine_id": exc.medicine_id,
                "medicine_name": exc.medicine_name,
                "reasoning": exc.reasoning,
                "rag_context": rag_context or {},
            },
        )
        run_in_background(send_push_to_token, user.push_token, f"Exception Agent Alert: {exc.medicine_name}", exc.patient_action, user.id)

    # Webhook for external systems
    dispatch_webhook(db, event_type="exception_escalated", payload={
        "exception_type": exc.exception_type,
        "escalation_level": exc.escalation_level,
        "severity": exc.severity,
        "medicine_id": exc.medicine_id,
        "medicine_name": exc.medicine_name,
        "patient_id": user.id if user else 0,
        "staff_action": exc.staff_action,
    })

    _out({
        "escalated_to": [s.role for s in targets],
        "staff_count": len(targets),
        "patient_notified": bool(user),
        "webhook": True,
    })


def _publish_exception_trace(db: Session, user: User | None, exc: ExceptionCase, rag_context: dict) -> None:
    """
    Publish admin-visible trace for every exception classification (including L1).
    """
    admins = db.query(User).filter(User.role == "admin").all()
    title = "Exception Agent Trace"
    body = f"{exc.exception_type} classified as {exc.escalation_level} for {exc.medicine_name}"
    metadata = {
        "agent_name": "exception_agent",
        "phase": "exception_classified",
        "exception_type": exc.exception_type,
        "escalation_level": exc.escalation_level,
        "severity": exc.severity,
        "medicine_id": exc.medicine_id,
        "medicine_name": exc.medicine_name,
        "reasoning": exc.reasoning,
        "target_user_id": user.id if user else None,
        "target_user_name": user.name if user else None,
        "target_user_email": user.email if user else None,
        "target_user_role": user.role if user else None,
        "rag_context": rag_context or {},
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIND ALTERNATIVES: When stock is exhausted
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="exception_find_alternatives")
def _find_alternatives(db: Session, medicine_id: int, medicine_name: str) -> list[dict]:
    """
    Find similar medicines when one is out of stock.
    Strategy: match by name keywords (e.g., "Omega" matches other Omega products).
    """
    med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not med:
        return []

    # Extract first meaningful keyword from name
    words = med.name.split()
    keywords = [w for w in words if len(w) > 3 and w.isalpha()]
    if not keywords:
        return []

    search = keywords[0]
    alternatives = (
        db.query(Medicine)
        .filter(
            Medicine.id != medicine_id,
            Medicine.stock > 0,
            Medicine.name.ilike(f"%{search}%"),
        )
        .order_by(Medicine.price.asc())
        .limit(3)
        .all()
    )

    alts = [
        {
            "medicine_id": a.id,
            "name": a.name,
            "pzn": a.pzn,
            "price": a.price,
            "stock": a.stock,
            "rx_required": a.rx_required,
            "reason": f"Similar to {medicine_name} (keyword: '{search}')",
        }
        for a in alternatives
    ]

    _out({"original": medicine_name, "keyword": search, "alternatives_found": len(alts),
          "alternatives": [a["name"] for a in alts]})
    return alts


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _is_controlled(medicine_name: str) -> bool:
    name_lower = medicine_name.lower()
    return any(kw in name_lower for kw in CONTROLLED_KEYWORDS)


def _parse_allergies(user: User) -> list[str]:
    if not user.allergies:
        return []
    return [a.strip().lower() for a in user.allergies.split(",") if a.strip()]


def _check_allergy_conflict(medicine_name: str, user_allergies: list[str]) -> dict | None:
    name_lower = medicine_name.lower()
    for allergy in user_allergies:
        # Direct name match
        if allergy in name_lower:
            return {"allergy": allergy, "match": "direct_name"}
        # Check conflict map
        conflicts = ALLERGY_CONFLICTS.get(allergy, [])
        for conflict_med in conflicts:
            if conflict_med.lower() in name_lower:
                return {"allergy": allergy, "match": conflict_med}
    return None


def _out(d):
    try:
        langfuse_context.update_current_observation(output=d)
    except Exception:
        pass