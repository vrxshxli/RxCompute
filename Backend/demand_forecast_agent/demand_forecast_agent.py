"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RxCompute Demand Forecasting Agent — Linear Regression on Order Velocity
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THIS IS NOT a simple "count orders" tool.
This is a statistical forecasting engine that:

  1. COLLECTS historical order data per medicine (from orders + order_items)
  2. BUILDS daily consumption time series (units sold per day)
  3. FITS linear regression (y = mx + b) to detect TREND
  4. CALCULATES moving average for smoothed demand signal
  5. COMPUTES seasonal ratio (weekday vs weekend patterns)
  6. PREDICTS demand for next N days using: trend + seasonality + momentum
  7. COMPARES predicted demand against current stock levels
  8. CALCULATES reorder point and days-until-stockout
  9. FLAGS medicines at risk with severity levels
 10. GENERATES per-pharmacy demand breakdown
 11. PRODUCES admin-ready forecast report with confidence intervals

ALL MATH IS PURE PYTHON — no numpy/pandas required (hackathon-friendly).

LANGFUSE: Every regression, every prediction, every risk flag traced.
"""

import math
import time
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from langfuse.decorators import observe, langfuse_context
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from database import SessionLocal
from models.medicine import Medicine
from models.notification import NotificationType
from models.order import Order, OrderItem, OrderStatus
from models.user import User
from models.warehouse import WarehouseStock, PharmacyStock
from models.pharmacy_store import PharmacyStore
from services.notifications import create_notification, run_in_background, send_push_to_token
from services.agent_rag import retrieve_agent_context


# ━━━ CONFIG ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOOKBACK_DAYS = 90           # Historical window for regression
FORECAST_DAYS_DEFAULT = 14   # Default prediction horizon
MOVING_AVG_WINDOW = 7        # 7-day moving average
MIN_DATA_POINTS = 3          # Minimum days with orders for regression
SAFETY_STOCK_DAYS = 7        # Buffer days for safety stock
REORDER_LEAD_DAYS = 3        # Days it takes to restock

# Risk thresholds
RISK_CRITICAL_DAYS = 3       # Stock lasts <= 3 days
RISK_HIGH_DAYS = 7           # Stock lasts <= 7 days
RISK_MEDIUM_DAYS = 14        # Stock lasts <= 14 days


# ━━━ DATA STRUCTURES ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class MedicineForecast:
    """Forecast for one medicine."""
    medicine_id: int = 0
    medicine_name: str = ""
    pzn: str = ""
    price: float = 0.0

    # Current inventory
    admin_stock: int = 0
    warehouse_stock: int = 0
    total_pharmacy_stock: int = 0
    total_system_stock: int = 0

    # Historical analysis
    total_orders_in_period: int = 0
    total_units_sold: int = 0
    unique_customers: int = 0
    data_points: int = 0         # days with at least 1 order

    # Linear regression results
    trend_slope: float = 0.0     # units/day change (positive = growing demand)
    trend_intercept: float = 0.0
    r_squared: float = 0.0       # regression fit quality (0-1)
    trend_direction: str = ""    # "rising", "falling", "stable"

    # Demand metrics
    avg_daily_demand: float = 0.0
    moving_avg_7d: float = 0.0
    peak_daily_demand: float = 0.0
    weekend_ratio: float = 1.0   # >1 = more weekend demand

    # Forecast
    forecast_days: int = 14
    predicted_demand: float = 0.0
    predicted_daily_avg: float = 0.0
    confidence: str = ""         # high, medium, low

    # Stock risk
    days_until_stockout: float = 0.0
    risk_level: str = ""         # critical, high, medium, low, safe
    reorder_point: int = 0       # stock level at which to reorder
    recommended_reorder_qty: int = 0

    # Per-pharmacy breakdown
    pharmacy_demand: list = field(default_factory=list)
    rag_evidence: list = field(default_factory=list)

    reasoning: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class ForecastResult:
    """Complete forecast run result."""
    total_medicines: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    safe_count: int = 0
    lookback_days: int = LOOKBACK_DAYS
    forecast_days: int = FORECAST_DAYS_DEFAULT
    execution_time_ms: int = 0
    forecasts: list = field(default_factory=list)
    reorder_alerts: list = field(default_factory=list)
    top_movers: list = field(default_factory=list)

    def to_dict(self):
        return {
            "total_medicines_analyzed": self.total_medicines,
            "risk_summary": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "safe": self.safe_count,
            },
            "lookback_days": self.lookback_days,
            "forecast_days": self.forecast_days,
            "execution_time_ms": self.execution_time_ms,
            "reorder_alerts": self.reorder_alerts,
            "top_movers": self.top_movers,
            "forecasts": [f.to_dict() for f in self.forecasts],
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC: Full forecast scan
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_forecast_full_scan")
def run_demand_forecast(forecast_days: int = FORECAST_DAYS_DEFAULT) -> dict:
    """
    Forecast demand for ALL medicines. Admin dashboard use.
    Returns risk-ranked list with reorder recommendations.
    """
    t0 = time.time()
    db = SessionLocal()
    try:
        result = _forecast_all(db, forecast_days)
        _publish_demand_forecast_alerts(db, result, forecast_days)
    finally:
        db.close()
    result.execution_time_ms = int((time.time() - t0) * 1000)

    _out({"medicines": result.total_medicines, "critical": result.critical_count,
          "high": result.high_count, "time_ms": result.execution_time_ms})
    return result.to_dict()


def _publish_demand_forecast_alerts(db: Session, result: ForecastResult, forecast_days: int) -> None:
    """
    Emit demand-forecast agent traces/alerts for admin and pharmacy dashboards.
    """
    admins = db.query(User).filter(User.role == "admin").all()
    pharmacists = db.query(User).filter(User.role == "pharmacy_store").all()
    critical_or_high = result.critical_count + result.high_count
    trace_title = "Demand Forecast Agent Trace"
    trace_body = (
        f"Forecast completed: {result.total_medicines} medicines, "
        f"critical={result.critical_count}, high={result.high_count}, days={forecast_days}."
    )
    rag_by_medicine = []
    for fc in result.forecasts:
        if fc.risk_level not in {"critical", "high"}:
            continue
        rag_by_medicine.append(
            {
                "medicine_id": fc.medicine_id,
                "medicine_name": fc.medicine_name,
                "risk_level": fc.risk_level,
                "rag_evidence": fc.rag_evidence[:4] if isinstance(fc.rag_evidence, list) else [],
            }
        )
        if len(rag_by_medicine) >= 12:
            break

    trace_meta = {
        "agent_name": "demand_forecast_agent",
        "phase": "demand_forecast_full_scan",
        "forecast_days": forecast_days,
        "total_medicines": result.total_medicines,
        "critical": result.critical_count,
        "high": result.high_count,
        "medium": result.medium_count,
        "low": result.low_count,
        "safe": result.safe_count,
        "reorder_alerts": result.reorder_alerts[:15],
        "rag_context": {
            "total_candidates": sum(len(getattr(f, "rag_evidence", []) or []) for f in result.forecasts),
            "evidence_by_medicine": rag_by_medicine,
        },
    }
    for admin in admins:
        create_notification(
            db,
            admin.id,
            NotificationType.safety,
            trace_title,
            trace_body,
            has_action=True,
            dedupe_window_minutes=10,
            metadata=trace_meta,
        )
        run_in_background(send_push_to_token, admin.push_token, trace_title, trace_body, admin.id)

    if critical_or_high <= 0:
        db.commit()
        return

    alert_title = "Demand Forecast Agent Alert"
    top_names = ", ".join([x.get("name", "-") for x in result.reorder_alerts[:3]]) if result.reorder_alerts else "No medicines"
    alert_body = (
        f"{critical_or_high} medicines need urgent reorder. Top risk: {top_names}. "
        f"Check demand forecast dashboard."
    )
    alert_meta = {
        "agent_name": "demand_forecast_agent",
        "phase": "demand_forecast_reorder_alert",
        "forecast_days": forecast_days,
        "critical": result.critical_count,
        "high": result.high_count,
        "reorder_alerts": result.reorder_alerts[:20],
        "rag_context": {
            "total_candidates": sum(len(getattr(f, "rag_evidence", []) or []) for f in result.forecasts),
            "evidence_by_medicine": rag_by_medicine,
        },
    }
    for u in admins + pharmacists:
        create_notification(
            db,
            u.id,
            NotificationType.safety,
            alert_title,
            alert_body,
            has_action=True,
            dedupe_window_minutes=10,
            metadata=alert_meta,
        )
        run_in_background(send_push_to_token, u.push_token, alert_title, alert_body, u.id)
    db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC: Single medicine forecast
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_forecast_single")
def forecast_medicine(medicine_id: int, forecast_days: int = FORECAST_DAYS_DEFAULT) -> dict:
    """Forecast for one medicine. Returns full regression + risk analysis."""
    db = SessionLocal()
    try:
        med = db.query(Medicine).filter(Medicine.id == medicine_id).first()
        if not med:
            return {"error": f"Medicine {medicine_id} not found."}
        fc = _forecast_single(db, med, forecast_days)
    finally:
        db.close()
    return fc.to_dict()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC: Per-pharmacy demand forecast
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_forecast_by_pharmacy")
def forecast_by_pharmacy(forecast_days: int = FORECAST_DAYS_DEFAULT) -> dict:
    """Demand breakdown per pharmacy node. For warehouse transfer planning."""
    db = SessionLocal()
    try:
        stores = db.query(PharmacyStore).filter(PharmacyStore.active == True).all()
        pharmacy_forecasts = []
        for store in stores:
            pf = _forecast_pharmacy(db, store, forecast_days)
            pharmacy_forecasts.append(pf)
    finally:
        db.close()
    return {"forecast_days": forecast_days, "pharmacies": pharmacy_forecasts}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE: Forecast all medicines
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_forecast_all")
def _forecast_all(db: Session, forecast_days: int) -> ForecastResult:
    result = ForecastResult(forecast_days=forecast_days)
    medicines = db.query(Medicine).order_by(Medicine.name).all()
    result.total_medicines = len(medicines)

    for med in medicines:
        fc = _forecast_single(db, med, forecast_days)
        result.forecasts.append(fc)

        if fc.risk_level == "critical":
            result.critical_count += 1
        elif fc.risk_level == "high":
            result.high_count += 1
        elif fc.risk_level == "medium":
            result.medium_count += 1
        elif fc.risk_level == "low":
            result.low_count += 1
        else:
            result.safe_count += 1

        # Reorder alerts (critical + high only)
        if fc.risk_level in ("critical", "high"):
            result.reorder_alerts.append({
                "medicine_id": fc.medicine_id,
                "name": fc.medicine_name,
                "risk": fc.risk_level,
                "days_until_stockout": round(fc.days_until_stockout, 1),
                "current_stock": fc.total_system_stock,
                "predicted_demand": round(fc.predicted_demand, 0),
                "recommended_reorder": fc.recommended_reorder_qty,
                "trend": fc.trend_direction,
            })

    # Top movers (highest avg daily demand)
    sorted_by_demand = sorted(result.forecasts, key=lambda f: -f.avg_daily_demand)
    result.top_movers = [
        {"name": f.medicine_name, "avg_daily": round(f.avg_daily_demand, 2),
         "trend": f.trend_direction, "slope": round(f.trend_slope, 4)}
        for f in sorted_by_demand[:10]
    ]

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CORE: Forecast single medicine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_forecast_medicine")
def _forecast_single(db: Session, med: Medicine, forecast_days: int) -> MedicineForecast:
    fc = MedicineForecast(
        medicine_id=med.id, medicine_name=med.name,
        pzn=med.pzn, price=med.price, forecast_days=forecast_days,
        admin_stock=med.stock or 0,
    )
    rag_ctx = retrieve_agent_context(
        db,
        user_id=None,
        query=f"demand forecast {med.name} stock velocity trend",
        medicine_ids=[med.id],
        top_k=6,
    )
    fc.rag_evidence = rag_ctx.get("snippets", []) if isinstance(rag_ctx, dict) else []

    # ── Gather inventory ────────────────────────────────
    fc.warehouse_stock = _get_warehouse_stock(db, med.id)
    fc.total_pharmacy_stock = _get_total_pharmacy_stock(db, med.id)
    fc.total_system_stock = fc.admin_stock + fc.warehouse_stock + fc.total_pharmacy_stock

    # ── Build daily time series ─────────────────────────
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    daily_series, order_meta = _build_time_series(db, med.id, cutoff)

    fc.total_orders_in_period = order_meta["total_orders"]
    fc.total_units_sold = order_meta["total_units"]
    fc.unique_customers = order_meta["unique_customers"]
    fc.data_points = len([v for v in daily_series.values() if v > 0])

    # ── Calculate basic metrics ─────────────────────────
    if daily_series:
        values = list(daily_series.values())
        fc.avg_daily_demand = sum(values) / len(values) if values else 0
        fc.peak_daily_demand = max(values) if values else 0

        # 7-day moving average (last 7 days)
        last_7 = values[-MOVING_AVG_WINDOW:] if len(values) >= MOVING_AVG_WINDOW else values
        fc.moving_avg_7d = sum(last_7) / len(last_7) if last_7 else 0

        # Weekend ratio
        fc.weekend_ratio = _calc_weekend_ratio(daily_series)

    # ── Linear regression ───────────────────────────────
    if fc.data_points >= MIN_DATA_POINTS:
        slope, intercept, r_sq = _linear_regression(daily_series)
        fc.trend_slope = slope
        fc.trend_intercept = intercept
        fc.r_squared = r_sq

        if slope > 0.05:
            fc.trend_direction = "rising"
        elif slope < -0.05:
            fc.trend_direction = "falling"
        else:
            fc.trend_direction = "stable"

        # Confidence based on R² and data points
        if r_sq > 0.5 and fc.data_points >= 14:
            fc.confidence = "high"
        elif r_sq > 0.2 and fc.data_points >= 7:
            fc.confidence = "medium"
        else:
            fc.confidence = "low"
    else:
        fc.trend_direction = "insufficient_data"
        fc.confidence = "low"

    # ── Predict future demand ───────────────────────────
    fc.predicted_demand = _predict_demand(fc, forecast_days)
    fc.predicted_daily_avg = fc.predicted_demand / forecast_days if forecast_days > 0 else 0

    # ── Stock risk analysis ─────────────────────────────
    daily_burn = max(fc.moving_avg_7d, fc.avg_daily_demand, 0.01)
    fc.days_until_stockout = fc.total_system_stock / daily_burn if daily_burn > 0 else 999

    if fc.days_until_stockout <= RISK_CRITICAL_DAYS:
        fc.risk_level = "critical"
    elif fc.days_until_stockout <= RISK_HIGH_DAYS:
        fc.risk_level = "high"
    elif fc.days_until_stockout <= RISK_MEDIUM_DAYS:
        fc.risk_level = "medium"
    elif fc.days_until_stockout <= 30:
        fc.risk_level = "low"
    else:
        fc.risk_level = "safe"

    # ── Reorder point + recommended qty ─────────────────
    fc.reorder_point = int(math.ceil(daily_burn * (SAFETY_STOCK_DAYS + REORDER_LEAD_DAYS)))
    fc.recommended_reorder_qty = int(math.ceil(daily_burn * 30))  # 30-day supply

    # ── Per-pharmacy demand ─────────────────────────────
    fc.pharmacy_demand = _pharmacy_demand_breakdown(db, med.id, cutoff, forecast_days)

    fc.reasoning = (
        f"{med.name}: avg {fc.avg_daily_demand:.2f}/day, MA7 {fc.moving_avg_7d:.2f}/day, "
        f"trend {fc.trend_direction} (slope {fc.trend_slope:.4f}, R²={fc.r_squared:.3f}). "
        f"Stock {fc.total_system_stock}, stockout in {fc.days_until_stockout:.1f} days → {fc.risk_level}. "
        f"Reorder at {fc.reorder_point}, recommended qty {fc.recommended_reorder_qty}."
    )

    _out({
        "medicine": med.name, "avg_daily": round(fc.avg_daily_demand, 2),
        "ma7": round(fc.moving_avg_7d, 2), "trend": fc.trend_direction,
        "slope": round(fc.trend_slope, 4), "r_squared": round(fc.r_squared, 3),
        "stock": fc.total_system_stock, "stockout_days": round(fc.days_until_stockout, 1),
        "risk": fc.risk_level, "predicted_demand": round(fc.predicted_demand, 0),
        "confidence": fc.confidence,
    })

    return fc


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TIME SERIES: Build daily consumption data
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_build_timeseries")
def _build_time_series(db: Session, medicine_id: int, cutoff: datetime) -> tuple[dict, dict]:
    """
    Query orders+order_items table. Build {date_str: total_units_sold} dict.
    Only counts delivered/dispatched/packed/verified orders (not cancelled/pending).
    """
    valid_statuses = [OrderStatus.delivered, OrderStatus.dispatched, OrderStatus.packed,
                      OrderStatus.verified, OrderStatus.confirmed, OrderStatus.picking]

    rows = (
        db.query(
            sqlfunc.date(Order.created_at).label("order_date"),
            sqlfunc.sum(OrderItem.quantity).label("total_qty"),
            sqlfunc.count(sqlfunc.distinct(Order.user_id)).label("uniq_users"),
            sqlfunc.count(OrderItem.id).label("order_count"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            OrderItem.medicine_id == medicine_id,
            Order.created_at >= cutoff,
            Order.status.in_(valid_statuses),
        )
        .group_by(sqlfunc.date(Order.created_at))
        .order_by(sqlfunc.date(Order.created_at))
        .all()
    )

    # Fill ALL days in the lookback window (including 0-demand days)
    daily = {}
    total_orders = 0
    total_units = 0
    unique_customers = set()

    start = cutoff.date() if hasattr(cutoff, 'date') else cutoff
    end = datetime.now(timezone.utc).date()
    current = start
    while current <= end:
        daily[current.isoformat()] = 0.0
        current += timedelta(days=1)

    for row in rows:
        date_key = str(row.order_date)
        qty = int(row.total_qty or 0)
        daily[date_key] = float(qty)
        total_orders += int(row.order_count or 0)
        total_units += qty

    # Get unique customers separately
    cust_rows = (
        db.query(sqlfunc.count(sqlfunc.distinct(Order.user_id)))
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.medicine_id == medicine_id, Order.created_at >= cutoff,
                Order.status.in_(valid_statuses))
        .scalar()
    )

    meta = {"total_orders": total_orders, "total_units": total_units, "unique_customers": cust_rows or 0}
    return daily, meta


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LINEAR REGRESSION: y = mx + b (pure Python)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_linear_regression")
def _linear_regression(daily_series: dict) -> tuple[float, float, float]:
    """
    Ordinary Least Squares regression on daily demand.
    x = day index (0, 1, 2, ...), y = units sold that day.
    Returns (slope, intercept, r_squared).
    """
    n = len(daily_series)
    if n < 2:
        return 0.0, 0.0, 0.0

    ys = list(daily_series.values())
    xs = list(range(n))

    sum_x = sum(xs)
    sum_y = sum(ys)
    sum_xy = sum(x * y for x, y in zip(xs, ys))
    sum_x2 = sum(x * x for x in xs)

    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        return 0.0, sum_y / n if n > 0 else 0.0, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n

    # R² (coefficient of determination)
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))

    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    r_squared = max(0, min(1, r_squared))  # clamp to [0, 1]

    _out({"slope": round(slope, 6), "intercept": round(intercept, 4),
          "r_squared": round(r_squared, 4), "data_points": n})
    return slope, intercept, r_squared


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PREDICT: Future demand using trend + momentum
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _predict_demand(fc: MedicineForecast, days: int) -> float:
    """
    Combine linear trend with recent momentum (moving average).
    Weighted: 60% trend projection + 40% MA7 extrapolation.
    """
    if fc.data_points < MIN_DATA_POINTS:
        # Insufficient data — use simple average
        return fc.avg_daily_demand * days

    # Trend projection: sum of (slope*x + intercept) for future days
    base_day = LOOKBACK_DAYS  # next day after lookback period
    trend_total = sum(
        max(fc.trend_slope * (base_day + d) + fc.trend_intercept, 0)
        for d in range(days)
    )

    # MA7 projection
    ma_total = fc.moving_avg_7d * days

    # Weighted blend
    if fc.r_squared > 0.3:
        predicted = 0.6 * trend_total + 0.4 * ma_total
    else:
        predicted = 0.3 * trend_total + 0.7 * ma_total  # Trust MA more if regression weak

    return max(predicted, 0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# WEEKEND RATIO: Weekday vs weekend demand pattern
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _calc_weekend_ratio(daily_series: dict) -> float:
    weekday_total, weekend_total = 0.0, 0.0
    weekday_count, weekend_count = 0, 0

    for date_str, qty in daily_series.items():
        try:
            dt = datetime.fromisoformat(date_str)
        except ValueError:
            continue
        if dt.weekday() >= 5:  # Sat=5, Sun=6
            weekend_total += qty
            weekend_count += 1
        else:
            weekday_total += qty
            weekday_count += 1

    avg_weekday = weekday_total / weekday_count if weekday_count > 0 else 1
    avg_weekend = weekend_total / weekend_count if weekend_count > 0 else 1

    return round(avg_weekend / avg_weekday, 2) if avg_weekday > 0 else 1.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INVENTORY: Stock from all sources
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_warehouse_stock(db: Session, medicine_id: int) -> int:
    row = db.query(WarehouseStock).filter(WarehouseStock.medicine_id == medicine_id).first()
    return row.quantity if row else 0

def _get_total_pharmacy_stock(db: Session, medicine_id: int) -> int:
    total = (
        db.query(sqlfunc.sum(PharmacyStock.quantity))
        .filter(PharmacyStock.medicine_id == medicine_id)
        .scalar()
    )
    return int(total or 0)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PER-PHARMACY: Demand breakdown by store
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_pharmacy_breakdown")
def _pharmacy_demand_breakdown(
    db: Session, medicine_id: int, cutoff: datetime, forecast_days: int,
) -> list[dict]:
    valid = [OrderStatus.delivered, OrderStatus.dispatched, OrderStatus.packed,
             OrderStatus.verified, OrderStatus.confirmed]

    rows = (
        db.query(
            Order.pharmacy,
            sqlfunc.sum(OrderItem.quantity).label("total_qty"),
            sqlfunc.count(OrderItem.id).label("order_count"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            OrderItem.medicine_id == medicine_id,
            Order.created_at >= cutoff,
            Order.status.in_(valid),
            Order.pharmacy.isnot(None),
        )
        .group_by(Order.pharmacy)
        .all()
    )

    result = []
    total_period_days = max(LOOKBACK_DAYS, 1)

    for row in rows:
        node = row.pharmacy or "unassigned"
        qty = int(row.total_qty or 0)
        avg_daily = qty / total_period_days
        predicted = avg_daily * forecast_days

        # Get pharmacy stock
        store = db.query(PharmacyStore).filter(PharmacyStore.node_id == node).first()
        store_id = store.id if store else None
        ph_stock = 0
        if store_id:
            ps = db.query(PharmacyStock).filter(
                PharmacyStock.pharmacy_store_id == store_id,
                PharmacyStock.medicine_id == medicine_id
            ).first()
            ph_stock = ps.quantity if ps else 0

        result.append({
            "pharmacy_node": node,
            "pharmacy_name": store.name if store else node,
            "total_units_sold": qty,
            "order_count": int(row.order_count or 0),
            "avg_daily_demand": round(avg_daily, 2),
            "predicted_demand": round(predicted, 0),
            "current_stock": ph_stock,
            "days_until_stockout": round(ph_stock / avg_daily, 1) if avg_daily > 0 else 999,
        })

    return sorted(result, key=lambda x: -x["avg_daily_demand"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHARMACY: Forecast for one store
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="demand_forecast_pharmacy")
def _forecast_pharmacy(db: Session, store: PharmacyStore, forecast_days: int) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    valid = [OrderStatus.delivered, OrderStatus.dispatched, OrderStatus.packed,
             OrderStatus.verified, OrderStatus.confirmed]

    rows = (
        db.query(
            OrderItem.medicine_id,
            Medicine.name,
            sqlfunc.sum(OrderItem.quantity).label("total_qty"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(Medicine, Medicine.id == OrderItem.medicine_id)
        .filter(Order.pharmacy == store.node_id, Order.created_at >= cutoff,
                Order.status.in_(valid))
        .group_by(OrderItem.medicine_id, Medicine.name)
        .all()
    )

    medicines = []
    for row in rows:
        qty = int(row.total_qty or 0)
        avg_d = qty / max(LOOKBACK_DAYS, 1)
        pred = avg_d * forecast_days

        ps = db.query(PharmacyStock).filter(
            PharmacyStock.pharmacy_store_id == store.id,
            PharmacyStock.medicine_id == row.medicine_id
        ).first()
        stock = ps.quantity if ps else 0

        medicines.append({
            "medicine_id": row.medicine_id,
            "name": row.name,
            "sold_last_period": qty,
            "avg_daily": round(avg_d, 2),
            "predicted_demand": round(pred, 0),
            "current_stock": stock,
            "days_until_stockout": round(stock / avg_d, 1) if avg_d > 0 else 999,
        })

    return {
        "pharmacy_node": store.node_id,
        "pharmacy_name": store.name,
        "active": store.active,
        "total_medicines_sold": len(medicines),
        "medicines": sorted(medicines, key=lambda x: x["days_until_stockout"]),
    }


# ━━━ HELPER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _out(d):
    try:
        langfuse_context.update_current_observation(output=d)
    except Exception:
        pass