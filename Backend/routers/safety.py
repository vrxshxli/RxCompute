"""
POST /safety/check — Run Safety Agent via LangGraph + Langfuse.

The Flutter app calls this BEFORE creating an order.
Flow: User picks medicines in chat → app calls this → shows results → then payment.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from saftery_policies_agents.graph import process_with_safety

router = APIRouter(prefix="/safety", tags=["Safety Agent"])


class SafetyItem(BaseModel):
    medicine_id: int
    name: str = ""
    quantity: int = 1
    prescription_file: str | None = None

class SafetyCheckRequest(BaseModel):
    items: list[SafetyItem]
    message: str = ""


@router.post("/check")
def run_safety_check(
    data: SafetyCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run the full LangGraph safety chain.
    Every call is traced in Langfuse for judges.

    Request:
    {
      "items": [
        {"medicine_id": 1, "name": "Omega-3", "quantity": 2},
        {"medicine_id": 4, "name": "Mucosolvan", "quantity": 1}
      ],
      "message": "I need omega 3 and mucosolvan"
    }

    Response:
    {
      "safe": false,
      "blocked": true,
      "has_warnings": false,
      "safety_results": [...],
      "safety_summary": "⛔ Mucosolvan: requires prescription...",
      "response_type": "safety_warning"
    }
    """
    if not data.items:
        raise HTTPException(status_code=400, detail="No items to check")

    matched = [
        {
            "medicine_id": it.medicine_id,
            "name": it.name,
            "quantity": it.quantity,
            "prescription_file": it.prescription_file,
        }
        for it in data.items
    ]

    result = process_with_safety(
        user_id=current_user.id,
        matched_medicines=matched,
        user_message=data.message,
    )

    return {
        "safe": not result.get("has_blocks", False),
        "blocked": result.get("has_blocks", False),
        "has_warnings": result.get("has_warnings", False),
        "safety_results": result.get("safety_results", []),
        "safety_summary": result.get("safety_summary", ""),
        "response_type": result.get("response_type", "chat"),
        "response_message": result.get("response_message", ""),
    }


@router.post("/check-single/{medicine_id}")
def check_one(
    medicine_id: int,
    quantity: int = 1,
    prescription_file: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Quick check for one medicine (used when adding to cart)."""
    result = process_with_safety(
        user_id=current_user.id,
        matched_medicines=[{
            "medicine_id": medicine_id,
            "name": "",
            "quantity": quantity,
            "prescription_file": prescription_file,
        }],
    )
    return {
        "safe": not result.get("has_blocks", False),
        "blocked": result.get("has_blocks", False),
        "safety_results": result.get("safety_results", []),
        "safety_summary": result.get("safety_summary", ""),
    }