import socket
import json
import math
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from config import SMTP_FROM_EMAIL, SMTP_HOST, SMTP_PORT, SMTP_USER
from database import get_db
from dependencies import get_current_user
from models.notification import Notification, NotificationType
from models.order import Order
from models.user import User
from models.warehouse import TransferDirection, TransferStatus, WarehouseStock, WarehouseTransfer
from schemas.notification import NotificationOut
from services.notifications import (
    create_notification,
    send_push_if_available,
    send_test_email,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _agent_flow_catalog(agent_name: str) -> dict:
    a = (agent_name or "").strip().lower()
    catalog = {
        "conversational_agent": {
            "fetch_from": ["user message/voice transcript", "medicine catalog API", "chat assistant intent parser (Gemini)"],
            "pass_to": ["order_agent", "safety_agent", "mobile/web chat UI"],
            "langfuse": {
                "enabled": False,
                "note": "Conversation intent traces are currently surfaced via notification metadata; Langfuse spans are limited for this agent.",
            },
        },
        "order_agent": {
            "fetch_from": ["chat payload (items/payment/location)", "user profile", "order history context"],
            "pass_to": ["safety_agent", "exception_agent", "scheduler_agent", "orders router/db"],
            "langfuse": {
                "enabled": False,
                "note": "Order orchestration is traced in agent notifications; downstream agents carry Langfuse spans.",
            },
        },
        "safety_agent": {
            "fetch_from": ["orders/order_items", "medicines", "user_medications", "OCR text from prescription image"],
            "pass_to": ["exception_agent", "orders router (approve/block)", "admin/pharmacy/user notifications"],
            "langfuse": {
                "enabled": True,
                "span_entry": "safety_agent",
                "spans": ["safety_load_medicines", "safety_evaluate_rules", "safety_prescription_ocr", "safety_interaction_rules"],
            },
        },
        "exception_agent": {
            "fetch_from": ["blocked/warning safety outputs", "order context", "medicine alternatives"],
            "pass_to": ["pharmacy exception queue", "admin traces", "user notifications"],
            "langfuse": {
                "enabled": True,
                "span_entry": "exception_agent",
                "spans": ["exception_handle_all", "exception_classify", "exception_find_alternatives", "exception_escalate"],
            },
        },
        "scheduler_agent": {
            "fetch_from": ["order location", "pharmacy/store availability", "distance/eligibility scoring"],
            "pass_to": ["orders router assignment", "admin trace stream", "pharmacy queue"],
            "langfuse": {
                "enabled": False,
                "note": "Scheduler execution is captured in metadata trace events.",
            },
        },
        "prediction_agent": {
            "fetch_from": ["orders history", "user medication timelines", "velocity/consumption stats", "RAG context"],
            "pass_to": ["refill alerts", "demand forecast trigger", "notifications"],
            "langfuse": {
                "enabled": True,
                "span_entry": "prediction_agent_full_scan",
                "spans": ["prediction_scan_all", "prediction_patient", "prediction_velocity", "prediction_create_alert"],
            },
        },
        "demand_forecast_agent": {
            "fetch_from": ["historical orders", "medicine-level demand series", "pharmacy breakdown"],
            "pass_to": ["reorder alerts", "admin/pharmacy dashboards", "notification traces"],
            "langfuse": {
                "enabled": True,
                "span_entry": "demand_forecast_full_scan",
                "spans": ["demand_build_timeseries", "demand_linear_regression", "demand_pharmacy_breakdown"],
            },
        },
        "admin_automation_agent": {
            "fetch_from": ["order status transitions", "automation step state machine"],
            "pass_to": ["admin workflow timeline", "order status notifications"],
            "langfuse": {
                "enabled": False,
                "note": "Automation step events are persisted as trace metadata notifications.",
            },
        },
    }
    return catalog.get(
        a,
        {
            "fetch_from": ["trace metadata", "notification body/title"],
            "pass_to": ["admin workflow timeline"],
            "langfuse": {"enabled": False, "note": "No explicit agent catalog entry was found."},
        },
    )


def _enrich_trace_metadata(title: str, body: str, metadata: dict | None, inferred_agent: str) -> dict:
    base = metadata.copy() if isinstance(metadata, dict) else {}
    flow = _agent_flow_catalog(inferred_agent)
    existing_fetch = base.get("data_fetch_from")
    if isinstance(existing_fetch, list):
        fetch_list = existing_fetch
    elif isinstance(existing_fetch, str) and existing_fetch.strip():
        fetch_list = [existing_fetch.strip()]
    else:
        fetch_list = []
    existing_pass = base.get("data_passed_to")
    if isinstance(existing_pass, list):
        pass_list = existing_pass
    elif isinstance(existing_pass, str) and existing_pass.strip():
        pass_list = [existing_pass.strip()]
    else:
        pass_list = []
    # Keep response backward compatible while adding explainability for both new and old traces.
    base.setdefault("agent_name", inferred_agent)
    base.setdefault("trace_explainability_version", "v1")
    base["data_fetch_from"] = list(dict.fromkeys(fetch_list + flow["fetch_from"]))
    base["data_passed_to"] = list(dict.fromkeys(pass_list + flow["pass_to"]))
    base["langfuse_trace"] = base.get("langfuse_trace") or flow["langfuse"]
    if "phase" not in base:
        txt = f"{title} {body}".lower()
        if "verify" in txt:
            base["phase"] = "verify"
        elif "assign" in txt or "scheduler" in txt:
            base["phase"] = "assign"
        elif "forecast" in txt:
            base["phase"] = "forecast"
        elif "predict" in txt:
            base["phase"] = "predict"
        elif "exception" in txt:
            base["phase"] = "exception"
        else:
            base["phase"] = "workflow"
    if "data_flow_summary" not in base:
        base["data_flow_summary"] = (
            f"{inferred_agent} fetched from {', '.join(base['data_fetch_from'][:3])} "
            f"and passed outputs to {', '.join(base['data_passed_to'][:3])}."
        )
    return base


@router.get("/", response_model=list[NotificationOut])
def list_notifications(
    limit: int = Query(default=120, ge=10, le=300),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all notifications for the current user."""
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )


@router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read."""
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.put("/read-all")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications as read."""
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read"}


def _run_test_delivery(current_user: User, db: Session):
    title = "RxCompute Test Notification"
    body = "This is a test for push/email delivery channels."
    create_notification(
        db,
        current_user.id,
        NotificationType.general,
        title,
        body,
        has_action=False,
    )
    db.commit()
    send_push_if_available(current_user, title, body)
    email_target = current_user.email or "rxcompute@35ddfa3956a414ee.maileroo.org"
    email_ok = send_test_email(
        recipient_email=email_target,
        subject="RxCompute Test Email",
        body="If you received this, custom SMTP is working.",
    )
    return {
        "push_token_present": bool(current_user.push_token),
        "email_target": email_target,
        "email_sent": email_ok,
        "note": "Check Render logs for push/email send errors if delivery fails.",
    }


def _smtp_probe(host: str, port: int, timeout_s: float = 2.0) -> dict:
    try:
        infos = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ips = [i[4][0] for i in infos]
    except Exception as exc:
        return {"host": host, "port": port, "ok": False, "error": f"dns_error: {exc}"}
    for ip in ips:
        try:
            with socket.create_connection((ip, port), timeout=timeout_s):
                return {"host": host, "port": port, "ok": True, "ip": ip}
        except Exception:
            continue
    return {"host": host, "port": port, "ok": False, "error": "connect_failed", "ips": ips[:4]}


@router.get("/delivery-health")
def delivery_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view delivery health")
    now = datetime.utcnow()
    since = now - timedelta(hours=24)
    smtp_ports = [SMTP_PORT, 587, 2525, 465]
    dedup_ports = []
    for p in smtp_ports:
        if p not in dedup_ports:
            dedup_ports.append(p)
    smtp_checks = [_smtp_probe(SMTP_HOST, p) for p in dedup_ports]

    users = db.query(User).all()
    push_count = sum(1 for u in users if (u.push_token or "").strip())
    pharmacy_users = [u for u in users if u.role == "pharmacy_store"]
    warehouse_users = [u for u in users if u.role == "warehouse"]
    admin_users = [u for u in users if u.role == "admin"]

    notifications_24h = db.query(Notification).filter(Notification.created_at >= since).count()
    orders_24h = db.query(Order).filter(Order.created_at >= since).count()
    warehouse_stock_count = db.query(WarehouseStock).count()
    transfers_pending = (
        db.query(WarehouseTransfer)
        .filter(
            WarehouseTransfer.direction == TransferDirection.warehouse_to_pharmacy,
            WarehouseTransfer.status.in_([TransferStatus.requested, TransferStatus.picking, TransferStatus.packed]),
        )
        .count()
    )

    return {
        "timestamp_utc": now.isoformat(),
        "smtp": {
            "host": SMTP_HOST,
            "configured_port": SMTP_PORT,
            "from_email": SMTP_FROM_EMAIL,
            "user_hint": f"{SMTP_USER[:4]}...{SMTP_USER[-10:]}" if SMTP_USER else "",
            "reachability": smtp_checks,
        },
        "push": {
            "users_with_push_token": push_count,
            "users_without_push_token": max(len(users) - push_count, 0),
        },
        "roles": {
            "admins": len(admin_users),
            "pharmacy_users": len(pharmacy_users),
            "warehouse_users": len(warehouse_users),
            "total_users": len(users),
        },
        "events_24h": {
            "notifications_created": notifications_24h,
            "orders_created": orders_24h,
        },
        "warehouse": {
            "warehouse_stock_rows": warehouse_stock_count,
            "outbound_transfers_pending": transfers_pending,
        },
    }


@router.get("/safety-events")
def list_safety_events(
    severity: str = Query(default="all"),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view safety events")
    q = (
        db.query(Notification, User)
        .join(User, User.id == Notification.user_id)
        .filter(Notification.type == NotificationType.safety)
    )
    sev = (severity or "all").strip().lower()
    if sev == "blocked":
        q = q.filter(or_(Notification.title.ilike("%blocked%"), Notification.body.ilike("%blocked%")))
    elif sev == "warning":
        q = q.filter(or_(Notification.title.ilike("%warning%"), Notification.body.ilike("%warning%")))
    elif sev != "all":
        raise HTTPException(status_code=400, detail="Invalid severity filter")

    if search:
        term = f"%{search.strip()}%"
        q = q.filter(
            or_(
                Notification.title.ilike(term),
                Notification.body.ilike(term),
                User.name.ilike(term),
                User.email.ilike(term),
                User.role.ilike(term),
            )
        )

    rows = q.order_by(Notification.created_at.desc()).limit(limit).all()
    out = []
    for notif, user in rows:
        text = f"{notif.title} {notif.body}".lower()
        row_severity = "blocked" if "blocked" in text else ("warning" if "warning" in text else "info")
        metadata = None
        if getattr(notif, "metadata_json", None):
            try:
                metadata = json.loads(notif.metadata_json)
            except Exception:
                metadata = None
        target_user = None
        if isinstance(metadata, dict) and isinstance(metadata.get("target_user_id"), int):
            target_user = db.query(User).filter(User.id == metadata["target_user_id"]).first()
        out.append(
            {
                "id": notif.id,
                "user_id": notif.user_id,
                "user_name": user.name,
                "user_email": user.email,
                "user_role": user.role,
                "title": notif.title,
                "body": notif.body,
                "is_read": notif.is_read,
                "created_at": notif.created_at,
                "severity": row_severity,
                "metadata": metadata,
                "target_user_id": target_user.id if target_user else (metadata.get("target_user_id") if isinstance(metadata, dict) else None),
                "target_user_name": target_user.name if target_user else (metadata.get("target_user_name") if isinstance(metadata, dict) else None),
                "target_user_email": target_user.email if target_user else (metadata.get("target_user_email") if isinstance(metadata, dict) else None),
                "target_user_role": target_user.role if target_user else (metadata.get("target_user_role") if isinstance(metadata, dict) else None),
            }
        )
    return out


def _infer_agent_name(title: str, body: str, metadata: dict | None) -> str:
    raw = ""
    if isinstance(metadata, dict):
        raw = str(metadata.get("agent_name") or "").strip().lower()
    if raw:
        return raw
    txt = f"{title} {body}".lower()
    if "prediction" in txt:
        return "prediction_agent"
    if "scheduler" in txt:
        return "scheduler_agent"
    if "exception" in txt:
        return "exception_agent"
    if "conversation" in txt or "conversational" in txt or "chat" in txt:
        return "conversational_agent"
    if "demand forecast" in txt or "demand_forecast" in txt:
        return "demand_forecast_agent"
    if "order agent" in txt or "order_agent" in txt:
        return "order_agent"
    return "safety_agent"


@router.get("/agent-traces")
def list_agent_traces(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    agent_name: str = Query(default="all"),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can view agent traces")

    q = (
        db.query(Notification)
        .filter(
            Notification.type == NotificationType.safety,
            or_(
                Notification.title.ilike("%agent%"),
                Notification.title.ilike("%trace%"),
                Notification.body.ilike("%agent%"),
                Notification.body.ilike("%trace%"),
                Notification.metadata_json.isnot(None),
            ),
        )
    )

    if search:
        term = f"%{search.strip()}%"
        q = q.filter(
            or_(
                Notification.title.ilike(term),
                Notification.body.ilike(term),
                Notification.metadata_json.ilike(term),
            )
        )

    agent_q = (agent_name or "all").strip().lower()
    if agent_q and agent_q != "all":
        token = agent_q.replace("_", " ").replace("-", " ")
        q = q.filter(
            or_(
                Notification.metadata_json.ilike(f"%{agent_q}%"),
                Notification.title.ilike(f"%{token}%"),
                Notification.body.ilike(f"%{token}%"),
            )
        )

    total = q.count()
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
    if page > total_pages and total > 0:
        page = total_pages
    offset = (page - 1) * page_size
    rows = q.order_by(Notification.created_at.desc()).offset(offset).limit(page_size).all()

    items = []
    discovered_agents = set()
    target_ids = set()
    recipient_ids = set()
    parsed_meta = {}
    for n in rows:
        meta = None
        if n.metadata_json:
            try:
                meta = json.loads(n.metadata_json)
            except Exception:
                meta = None
        parsed_meta[n.id] = meta
        recipient_ids.add(n.user_id)
        if isinstance(meta, dict) and isinstance(meta.get("target_user_id"), int):
            target_ids.add(meta["target_user_id"])

    user_map = {}
    all_lookup_ids = set(target_ids) | set(recipient_ids)
    if all_lookup_ids:
        targets = db.query(User).filter(User.id.in_(list(all_lookup_ids))).all()
        user_map = {u.id: u for u in targets}

    for n in rows:
        meta = parsed_meta.get(n.id)
        inferred = _infer_agent_name(n.title, n.body, meta)
        discovered_agents.add(inferred)
        target_user = None
        target_user_id = None
        if isinstance(meta, dict) and isinstance(meta.get("target_user_id"), int):
            target_user_id = meta["target_user_id"]
            target_user = user_map.get(target_user_id)
        recipient_user = user_map.get(n.user_id)
        enriched_meta = _enrich_trace_metadata(n.title or "", n.body or "", meta, inferred)
        items.append(
            {
                "id": n.id,
                "agent_name": inferred,
                "title": n.title,
                "body": n.body,
                "trace_id": f"trace-{n.id}",
                "is_read": n.is_read,
                "created_at": n.created_at,
                "metadata": enriched_meta,
                "target_user_id": target_user.id if target_user else target_user_id,
                "target_user_name": target_user.name if target_user else (meta.get("target_user_name") if isinstance(meta, dict) else None),
                "target_user_email": target_user.email if target_user else (meta.get("target_user_email") if isinstance(meta, dict) else None),
                "target_user_role": target_user.role if target_user else (meta.get("target_user_role") if isinstance(meta, dict) else None),
                "recipient_user_id": n.user_id,
                "recipient_user_name": recipient_user.name if recipient_user else None,
                "recipient_user_email": recipient_user.email if recipient_user else None,
                "recipient_user_role": recipient_user.role if recipient_user else None,
            }
        )

    # Build agent options from full filtered dataset, so admin can switch quickly.
    # Keep this lightweight by looking up only metadata/title/body signatures.
    all_rows = q.with_entities(Notification.title, Notification.body, Notification.metadata_json).limit(1000).all()
    for title, body, metadata_json in all_rows:
        m = None
        if metadata_json:
            try:
                m = json.loads(metadata_json)
            except Exception:
                m = None
        discovered_agents.add(_infer_agent_name(title or "", body or "", m))

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "agent_options": sorted(a for a in discovered_agents if a),
        "items": items,
    }


@router.post("/test-delivery")
def test_delivery_post(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create one test notification and attempt both push + email delivery."""
    return _run_test_delivery(current_user, db)


@router.get("/test-delivery")
def test_delivery_get(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Browser-friendly test route for push/email delivery."""
    return _run_test_delivery(current_user, db)
