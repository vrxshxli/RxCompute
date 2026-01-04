from fastapi import APIRouter, Depends
from .security import get_current_claims

router = APIRouter(prefix="/user", tags=["user-dashboard"])

@router.get("/overview")
async def overview(claims=Depends(get_current_claims)):
    return {
        "active_medicines": [
            {"name": "Amlodipine", "dose": "5 mg", "purpose": "BP", "doctor": "Dr. Mehta"},
            {"name": "Metformin", "dose": "500 mg", "purpose": "Diabetes", "doctor": "Dr. Rao"},
        ],
        "today_schedule": [
            {"time": "09:00", "text": "Take BP tablet"},
            {"time": "21:00", "text": "Take BP tablet"},
        ],
        "refill_alerts": [
            {"text": "Insulin will finish in 3 days", "action": "reorder", "medicine": "Insulin"}
        ],
    }

@router.get("/orders")
async def orders(claims=Depends(get_current_claims)):
    return {
        "items": [
            {"id": "ORD-1001", "status": "Completed", "date": "2025-12-12", "total": 740.0},
            {"id": "ORD-1002", "status": "Out for delivery", "date": "2026-01-03", "total": 520.0},
        ]
    }

@router.get("/orders/{order_id}")
async def order_detail(order_id: str, claims=Depends(get_current_claims)):
    return {
        "id": order_id,
        "status": "Completed",
        "invoice_url": "https://example.com/invoice.pdf",
        "qr_url": "https://example.com/qr.png",
        "payment_method": "UPI",
        "address": "Home, Pune, MH",
        "items": [
            {"name": "Amlodipine", "qty": 30, "price": 120.0},
            {"name": "Metformin", "qty": 60, "price": 400.0},
        ],
    }

@router.post("/orders/{order_id}/refill")
async def order_refill(order_id: str, claims=Depends(get_current_claims)):
    return {"ok": True, "order_id": order_id, "new_order_id": "ORD-2001"}

@router.get("/refill/suggestions")
async def refill_suggestions(claims=Depends(get_current_claims)):
    return {
        "recommended": [
            {"name": "Amlodipine", "reason": "Projected to finish in 5 days"},
        ],
        "missed": [
            {"name": "BP tablets", "note": "You usually buy every 30 days; last was 45 days ago"}
        ],
        "auto_remind": False,
    }

@router.get("/locker")
async def locker(claims=Depends(get_current_claims)):
    return {
        "medicines": [
            {"name": "Amlodipine", "dosage": "5 mg", "frequency": "2/day", "times": ["09:00","21:00"], "tags": ["Chronic"]},
            {"name": "Amoxicillin", "dosage": "500 mg", "frequency": "3/day", "times": ["08:00","14:00","20:00"], "tags": ["Short-term"]},
        ]
    }

@router.get("/reminders")
async def reminders(claims=Depends(get_current_claims)):
    return {
        "channels": {"push": True, "whatsapp": False, "email": True},
        "snooze_minutes": 10,
        "schedule": [
            {"medicine": "Amlodipine", "times": ["09:00","21:00"], "enabled": True},
        ],
        "notifications": [
            {"type": "reminder", "text": "Take BP tablet", "ts": "2026-01-04T09:00:00"},
            {"type": "order", "text": "Order shipped ORD-1002", "ts": "2026-01-04T10:15:00"},
        ],
    }

@router.get("/docs")
async def docs(claims=Depends(get_current_claims)):
    return {
        "prescriptions": [
            {"id": "RX-1", "file": "https://example.com/rx1.pdf", "expires": "2026-04-01", "linked_order": "ORD-1001", "rx_required": True}
        ],
        "invoices": [
            {"order_id": "ORD-1001", "file": "https://example.com/invoice.pdf"}
        ]
    }

@router.get("/profiles")
async def profiles(claims=Depends(get_current_claims)):
    return {
        "active": "self",
        "list": [
            {"id": "self", "name": "You", "tags": ["BP"]},
            {"id": "parent", "name": "Parent", "tags": ["Diabetes"]},
        ]
    }

@router.post("/safety/checks")
async def safety_checks(claims=Depends(get_current_claims)):
    return {
        "warnings": [
            {"title": "Interaction risk", "detail": "Amlodipine with grapefruit"},
            {"title": "Expired med", "detail": "Amoxicillin expired 2025-12-31"}
        ]
    }

@router.post("/ai/ask")
async def ai_ask(payload: dict, claims=Depends(get_current_claims)):
    q = payload.get("q", "")
    return {"answer": f"Stub: For your question '{q}', consult a pharmacist.", "sources": []}

@router.get("/account/addresses")
async def addresses(claims=Depends(get_current_claims)):
    return {"items": [
        {"id": "home", "label": "Home", "line": "Pune, MH"},
        {"id": "office", "label": "Office", "line": "Baner, Pune"},
    ]}

@router.get("/account/payments")
async def payments(claims=Depends(get_current_claims)):
    return {"items": [
        {"id": "pm1", "type": "card", "masked": "**** 4242"},
        {"id": "pm2", "type": "upi", "masked": "abc@okicici"},
    ]}

@router.get("/support/tickets")
async def tickets(claims=Depends(get_current_claims)):
    return {"items": [
        {"id": "TKT-1", "status": "Open", "subject": "Late delivery"}
    ]}

@router.get("/settings")
async def settings(claims=Depends(get_current_claims)):
    return {
        "language": "en",
        "ai_recommendations": True,
        "gdpr": {"download_available": False}
    }
