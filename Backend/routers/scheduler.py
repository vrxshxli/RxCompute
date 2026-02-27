"""
Scheduler Agent API — Virtual Pharmacy Grid

  POST /scheduler/route         → Route order to best pharmacy
  GET  /scheduler/grid-status   → All pharmacies with live scores (admin)
  POST /scheduler/simulate      → Dry run for demo (no side effects)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from models.pharmacy_store import PharmacyStore
from scheduler_agent.scheduler_agent import route_order_to_pharmacy

router = APIRouter(prefix="/scheduler", tags=["Scheduler Agent"])
STAFF = {"admin", "pharmacy_store", "warehouse"}


class RouteReq(BaseModel):
    order_items: list[dict] = []


@router.post("/route")
def route_order(data: RouteReq, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Route order to optimal pharmacy. Full Langfuse trace."""
    return route_order_to_pharmacy(user_id=user.id, order_items=data.order_items)


@router.get("/grid-status")
def grid_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Full grid with live scores — for admin dashboard."""
    if user.role not in STAFF:
        raise HTTPException(403, "Staff only")
    result = route_order_to_pharmacy(user_id=user.id, order_items=[])
    stores = db.query(PharmacyStore).order_by(PharmacyStore.node_id).all()
    ev_map = {e.get("node_id", ""): e for e in result.get("evaluations", [])}
    grid = [{
        "node_id": s.node_id, "name": s.name, "location": s.location,
        "active": s.active, "load": s.load or 0, "stock_count": s.stock_count or 0,
        "score": ev_map.get(s.node_id, {}).get("total", 0),
        "distance_km": ev_map.get(s.node_id, {}).get("distance_km", 0),
        "eta_min": ev_map.get(s.node_id, {}).get("eta_min", 0),
        "disqualified": ev_map.get(s.node_id, {}).get("disqualified", False),
        "reasoning": ev_map.get(s.node_id, {}).get("reasoning", ""),
    } for s in stores]
    return {"total": len(grid), "active": sum(1 for g in grid if g["active"]),
            "recommended": result.get("assigned_pharmacy", ""), "grid": grid}


@router.post("/simulate")
def simulate(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Dry run — judges see full Langfuse trace, no side effects."""
    if user.role not in STAFF:
        raise HTTPException(403, "Staff only")
    result = route_order_to_pharmacy(user_id=user.id, order_items=[])
    w = result.get("assigned_pharmacy")
    if w and not result.get("fallback_used"):
        s = db.query(PharmacyStore).filter(PharmacyStore.node_id == w).first()
        if s and (s.load or 0) > 0:
            s.load -= 1; db.commit()
    return {"simulation": True, "note": "Load restored. Check Langfuse.", **result}
