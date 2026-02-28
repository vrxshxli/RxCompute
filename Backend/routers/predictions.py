"""
Prediction Agent API — Refill Intelligence

  POST /predictions/scan           → Full scan all patients (admin/cron)
  GET  /predictions/me             → My medications with predictions
  GET  /predictions/demand         → Demand forecast for next N days (admin)
  POST /predictions/patient/{id}   → Predict for specific patient (admin)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from prediction_agent.prediction_agent import (
    run_prediction_scan,
    run_prediction_for_user,
    run_demand_forecast,
)

router = APIRouter(prefix="/predictions", tags=["Prediction Agent"])
STAFF = {"admin", "pharmacy_store", "warehouse"}


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
    return run_prediction_for_user(current_user.id)


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
    return run_prediction_for_user(user_id)