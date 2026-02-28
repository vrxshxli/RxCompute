"""
Demand Forecasting Agent API

  GET  /demand-forecast/                → Full forecast all medicines
  GET  /demand-forecast/medicine/{id}   → Single medicine deep forecast
  GET  /demand-forecast/by-pharmacy     → Per-pharmacy demand breakdown
  GET  /demand-forecast/reorder-alerts  → Only critical + high risk medicines
  GET  /demand-forecast/top-movers      → Top 10 fastest-moving medicines
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models.user import User
from demand_forecast_agent.demand_forecast_agent import (
    run_demand_forecast,
    forecast_medicine,
    forecast_by_pharmacy,
)

router = APIRouter(prefix="/demand-forecast", tags=["Demand Forecasting Agent"])
STAFF = {"admin", "pharmacy_store", "warehouse"}


@router.get("/")
def full_forecast(
    days: int = Query(default=14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Full demand forecast for ALL medicines.

    Uses linear regression on 90-day order history to predict
    demand for the next N days. Returns risk-ranked list with
    reorder recommendations.

    Langfuse trace shows regression coefficients, R², trend direction
    for every medicine.
    """
    if current_user.role not in STAFF:
        raise HTTPException(403, "Staff only")
    return run_demand_forecast(days)


@router.get("/medicine/{medicine_id}")
def single_medicine(
    medicine_id: int,
    days: int = Query(default=14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deep forecast for one medicine. Shows:
    - Linear regression (slope, intercept, R²)
    - Daily time series analysis
    - 7-day moving average
    - Weekend/weekday ratio
    - Stock risk + days until stockout
    - Reorder point + recommended quantity
    - Per-pharmacy demand breakdown
    """
    if current_user.role not in STAFF:
        raise HTTPException(403, "Staff only")
    return forecast_medicine(medicine_id, days)


@router.get("/by-pharmacy")
def pharmacy_breakdown(
    days: int = Query(default=14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Per-pharmacy demand forecast.
    Shows which pharmacy needs which medicine and how urgently.
    For warehouse transfer planning.
    """
    if current_user.role not in STAFF:
        raise HTTPException(403, "Staff only")
    return forecast_by_pharmacy(days)


@router.get("/reorder-alerts")
def reorder_alerts(
    days: int = Query(default=14, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Only critical + high risk medicines that need reordering NOW."""
    if current_user.role not in STAFF:
        raise HTTPException(403, "Staff only")
    result = run_demand_forecast(days)
    return {
        "reorder_alerts": result.get("reorder_alerts", []),
        "critical": result.get("risk_summary", {}).get("critical", 0),
        "high": result.get("risk_summary", {}).get("high", 0),
    }


@router.get("/top-movers")
def top_movers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Top 10 fastest-selling medicines by average daily demand."""
    if current_user.role not in STAFF:
        raise HTTPException(403, "Staff only")
    result = run_demand_forecast(14)
    return {"top_movers": result.get("top_movers", [])}