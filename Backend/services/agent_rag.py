"""
Agent RAG retrieval helpers.

Purpose:
- Build a lightweight retrieval layer over DB entities (medicine, user meds, recent orders)
- Return relevant context snippets for AI-agent style orchestration
- Keep retrieval read-only and deterministic
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from models.medicine import Medicine
from models.order import Order, OrderItem
from models.user_medication import UserMedication


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 1}


def _score(doc_text: str, query_tokens: set[str], boost: float = 0.0) -> float:
    if not query_tokens:
        return max(boost, 0.0)
    doc_tokens = _tokens(doc_text)
    if not doc_tokens:
        return 0.0
    overlap = len(doc_tokens & query_tokens)
    return overlap + boost


def retrieve_agent_context(
    db: Session,
    *,
    user_id: int | None,
    query: str,
    medicine_ids: list[int] | None = None,
    top_k: int = 8,
) -> dict[str, Any]:
    """
    Read-only retrieval context for agents.
    Returns ranked context snippets from:
      - medicines catalog
      - user_medications tracking
      - recent delivered/dispatched/verified order history
    """
    q_tokens = _tokens(query)
    med_ids = [int(x) for x in (medicine_ids or []) if isinstance(x, int)]
    ranked: list[tuple[float, dict[str, Any]]] = []

    # 1) Medicines retrieval
    meds_q = db.query(Medicine)
    if med_ids:
        meds_q = meds_q.filter(Medicine.id.in_(med_ids))
    meds = meds_q.order_by(Medicine.name.asc()).limit(80).all()
    for m in meds:
        txt = f"{m.name} {m.pzn or ''} {m.package or ''} {m.description or ''}"
        boost = 2.0 if m.id in med_ids else 0.0
        s = _score(txt, q_tokens, boost=boost)
        if s <= 0 and med_ids and m.id in med_ids:
            s = 1.0
        if s > 0:
            ranked.append(
                (
                    s,
                    {
                        "source": "medicine",
                        "medicine_id": m.id,
                        "name": m.name,
                        "pzn": m.pzn,
                        "rx_required": bool(m.rx_required),
                        "stock": int(m.stock or 0),
                        "price": float(m.price or 0),
                        "package": m.package,
                    },
                )
            )

    if user_id:
        # 2) User medication tracking retrieval
        um_rows = (
            db.query(UserMedication, Medicine)
            .outerjoin(Medicine, Medicine.id == UserMedication.medicine_id)
            .filter(UserMedication.user_id == user_id)
            .limit(100)
            .all()
        )
        for um, med in um_rows:
            med_name = med.name if med else (um.custom_name or "Medication")
            txt = f"{med_name} {um.dosage_instruction or ''}"
            boost = 1.8 if (med and med.id in med_ids) else 0.0
            s = _score(txt, q_tokens, boost=boost)
            if s > 0:
                ranked.append(
                    (
                        s,
                        {
                            "source": "user_medication",
                            "medication_id": um.id,
                            "medicine_id": um.medicine_id,
                            "medicine_name": med_name,
                            "frequency_per_day": int(um.frequency_per_day or 1),
                            "quantity_units": int(um.quantity_units or 0),
                            "dosage_instruction": um.dosage_instruction,
                            "created_at": um.created_at.isoformat() if um.created_at else None,
                        },
                    )
                )

        # 3) Recent order history retrieval
        cutoff = datetime.now(timezone.utc) - timedelta(days=120)
        order_rows = (
            db.query(Order, OrderItem)
            .join(OrderItem, OrderItem.order_id == Order.id)
            .filter(Order.user_id == user_id, Order.created_at >= cutoff)
            .order_by(Order.created_at.desc())
            .limit(140)
            .all()
        )
        for order, item in order_rows:
            txt = f"{item.name or ''} {order.order_uid or ''} {order.status.value if hasattr(order.status, 'value') else order.status}"
            boost = 1.5 if (item.medicine_id in med_ids) else 0.0
            s = _score(txt, q_tokens, boost=boost)
            if s > 0:
                ranked.append(
                    (
                        s,
                        {
                            "source": "order_history",
                            "order_id": order.id,
                            "order_uid": order.order_uid,
                            "status": order.status.value if hasattr(order.status, "value") else str(order.status),
                            "medicine_id": item.medicine_id,
                            "medicine_name": item.name,
                            "quantity": int(item.quantity or 0),
                            "strips_count": int(item.strips_count or 0),
                            "created_at": order.created_at.isoformat() if order.created_at else None,
                            "pharmacy": order.pharmacy,
                        },
                    )
                )

    ranked.sort(key=lambda x: x[0], reverse=True)
    snippets = [payload for _, payload in ranked[: max(top_k, 1)]]
    return {
        "query": query,
        "user_id": user_id,
        "medicine_ids": med_ids,
        "total_candidates": len(ranked),
        "snippets": snippets,
    }

