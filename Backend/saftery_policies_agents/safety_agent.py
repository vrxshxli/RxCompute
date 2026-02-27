"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RxCompute Safety Agent — LangGraph Node with Langfuse Tracing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PURPOSE:
  Sits between the Conversation Agent and Order creation.
  Checks EVERY medicine against safety rules before allowing orders.

USE CASES HANDLED:
  BLOCKS (order cannot proceed):
    1. Prescription required but not uploaded
    2. Medicine completely out of stock (stock = 0)
    3. Ordering more units than available in stock
    4. Medicine ID not found in database

  WARNINGS (order proceeds, user is informed):
    5. Stock is low (< 10 units) — might sell out soon
    6. Unusually high quantity (> 5) — possible misuse flag

  APPROVED (silent pass):
    7. Normal order — in stock, no prescription needed
    8. Rx medicine WITH valid prescription uploaded

WHY DETERMINISTIC (no LLM):
  Safety decisions must be 100% predictable and auditable.
  A judge must be able to verify: "if rx_required=True and
  prescription_file=None, the order is ALWAYS blocked."
  An LLM might hallucinate a different answer on different runs.

LANGFUSE TRACING:
  Every function decorated with @observe creates a "span" in Langfuse.
  The public Langfuse dashboard shows:
    - Which medicines were checked
    - Which rules fired and why
    - The reasoning chain for each decision
    - Total processing time
  This is a MANDATORY hackathon requirement.
"""

import time
from langfuse.decorators import observe, langfuse_context
from database import SessionLocal
from models.medicine import Medicine
from saftery_policies_agents.state import AgentState, SafetyCheckResult


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PUBLIC: LangGraph Node Entry Point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="safety_agent")
def run_safety_agent(state: AgentState) -> dict:
    """
    LangGraph node function.

    Called automatically by LangGraph when the chain reaches
    the "safety_check" step. Reads matched_medicines from state,
    checks each one, writes results back to state.

    This entire function call appears as one "span" in Langfuse.
    Inside it, each sub-function creates nested spans so judges
    can drill into the reasoning.
    """
    start = time.time()
    matched = state.get("matched_medicines", [])

    # ── Nothing to check ────────────────────────────────
    if not matched:
        _langfuse_output({
            "skipped": True,
            "reason": "no medicines in cart",
            "duration_ms": _elapsed(start),
        })
        return {
            **state,
            "safety_results": [],
            "has_blocks": False,
            "has_warnings": False,
            "safety_summary": "No medicines to check.",
        }

    # ── Load from DB + check rules ──────────────────────
    db = SessionLocal()
    try:
        results = _load_and_check_all(db, matched)
    finally:
        db.close()

    # ── Categorize ──────────────────────────────────────
    blocks   = [r for r in results if r["status"] == "blocked"]
    warnings = [r for r in results if r["status"] == "warning"]
    approved = [r for r in results if r["status"] == "approved"]

    has_blocks = len(blocks) > 0
    has_warnings = len(warnings) > 0
    summary = _build_summary(blocks, warnings, approved)

    # ── Log full results to Langfuse ────────────────────
    _langfuse_output({
        "total_medicines_checked": len(results),
        "blocked_count": len(blocks),
        "blocked_medicines": [b["medicine_name"] for b in blocks],
        "blocked_rules": [b["rule"] for b in blocks],
        "warning_count": len(warnings),
        "warning_medicines": [w["medicine_name"] for w in warnings],
        "approved_count": len(approved),
        "approved_medicines": [a["medicine_name"] for a in approved],
        "overall_verdict": "BLOCKED" if has_blocks else ("WARNINGS" if has_warnings else "ALL_CLEAR"),
        "duration_ms": _elapsed(start),
    })

    # ── Write results to state ──────────────────────────
    updated = {
        **state,
        "safety_results": results,
        "has_blocks": has_blocks,
        "has_warnings": has_warnings,
        "safety_summary": summary,
    }

    if has_blocks:
        updated["response_type"] = "safety_warning"
        updated["response_message"] = summary

    return updated


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTERNAL: Load medicines from DB and check all
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="safety_load_medicines")
def _load_and_check_all(db, matched: list[dict]) -> list[SafetyCheckResult]:
    """
    Single DB query to load all medicines, then check each.
    This is a separate Langfuse span so judges can see DB access time.
    """

    # One query, not N queries — production optimization
    med_ids = [m["medicine_id"] for m in matched]
    db_medicines = db.query(Medicine).filter(Medicine.id.in_(med_ids)).all()
    med_map = {m.id: m for m in db_medicines}

    _langfuse_output({
        "requested_ids": med_ids,
        "found_in_db": len(med_map),
        "missing_ids": [mid for mid in med_ids if mid not in med_map],
    })

    results: list[SafetyCheckResult] = []

    for item in matched:
        mid = item["medicine_id"]
        qty = item.get("quantity", 1)
        rx_file = item.get("prescription_file")

        med = med_map.get(mid)

        # USE CASE 4: Medicine not found in database
        if not med:
            results.append(SafetyCheckResult(
                medicine_id=mid,
                medicine_name=f"Unknown (ID: {mid})",
                status="blocked",
                rule="medicine_not_found",
                message=f"Medicine with ID {mid} was not found in our database.",
            ))
            continue

        result = _evaluate_rules(med, qty, rx_file)
        results.append(result)

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTERNAL: Evaluate all 5 safety rules for one medicine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="safety_evaluate_rules")
def _evaluate_rules(
    med: Medicine,
    qty: int,
    rx_file: str | None,
) -> SafetyCheckResult:
    """
    Run the 5-rule engine against one medicine.
    Priority order: first BLOCK wins, then first WARNING, then APPROVED.

    Each evaluation is a separate Langfuse span with full reasoning,
    so judges can see exactly why each medicine was approved/blocked.
    """

    stock = med.stock or 0
    name = med.name

    # ────────────────────────────────────────────────────
    # RULE 1: Prescription Required
    # ────────────────────────────────────────────────────
    # USE CASE 1: Mucosolvan (rx_required=True), no prescription → BLOCK
    # USE CASE 8: Mucosolvan WITH prescription → PASS (continues to next rules)
    #
    if med.rx_required and not rx_file:
        reasoning = (
            f"Medicine '{name}' has rx_required=True in database. "
            f"User did NOT provide a prescription_file (value: {rx_file}). "
            f"DECISION: BLOCK — patient must upload prescription before ordering."
        )
        _langfuse_output({"rule": "prescription_required", "status": "BLOCKED", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="blocked",
            rule="prescription_required",
            message=f"{name} requires a valid prescription. Please upload your prescription to proceed.",
        )

    # ────────────────────────────────────────────────────
    # RULE 2: Completely Out of Stock
    # ────────────────────────────────────────────────────
    # USE CASE 2: Bisoprolol (stock=0) → BLOCK
    #
    if stock == 0:
        reasoning = (
            f"Medicine '{name}' has stock=0 in database. "
            f"Cannot fulfill any quantity. "
            f"DECISION: BLOCK — medicine is out of stock."
        )
        _langfuse_output({"rule": "out_of_stock", "status": "BLOCKED", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="blocked",
            rule="out_of_stock",
            message=f"{name} is currently out of stock. We'll notify you when it's available.",
        )

    # ────────────────────────────────────────────────────
    # RULE 3: Requesting More Than Available
    # ────────────────────────────────────────────────────
    # USE CASE 3: User wants 50 Panthenol but stock=23 → BLOCK
    #
    if qty > stock:
        reasoning = (
            f"Medicine '{name}' has stock={stock}. "
            f"User requested quantity={qty}, which exceeds available stock. "
            f"DECISION: BLOCK — insufficient inventory. Max orderable: {stock}."
        )
        _langfuse_output({"rule": "insufficient_stock", "status": "BLOCKED", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="blocked",
            rule="insufficient_stock",
            message=f"Only {stock} units of {name} available, but you requested {qty}. Maximum you can order: {stock}.",
        )

    # ────────────────────────────────────────────────────
    # RULE 4: Low Stock Warning
    # ────────────────────────────────────────────────────
    # USE CASE 5: Omeprazole (stock=5) → WARN but allow
    #
    if stock < 10:
        reasoning = (
            f"Medicine '{name}' has stock={stock} (below threshold of 10). "
            f"Order CAN proceed but user should be warned. "
            f"DECISION: WARNING — low stock alert."
        )
        _langfuse_output({"rule": "low_stock", "status": "WARNING", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="warning",
            rule="low_stock",
            message=f"Low stock alert: only {stock} units of {name} remaining. Your order will proceed.",
        )

    # ────────────────────────────────────────────────────
    # RULE 5: Unusually High Quantity
    # ────────────────────────────────────────────────────
    # USE CASE 6: 8 boxes of Paracetamol → WARN (possible misuse)
    #
    if qty > 5:
        reasoning = (
            f"Medicine '{name}' ordered in quantity={qty} (above threshold of 5). "
            f"This is flagged as unusual for a single patient order. "
            f"DECISION: WARNING — may require pharmacist review."
        )
        _langfuse_output({"rule": "high_quantity", "status": "WARNING", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="warning",
            rule="high_quantity",
            message=f"Large order flagged: {qty} units of {name}. Orders above 5 units may require pharmacist review.",
        )

    # ────────────────────────────────────────────────────
    # ALL RULES PASSED
    # ────────────────────────────────────────────────────
    # USE CASE 7: Normal order (Omega-3, stock=47, qty=1) → APPROVED
    # USE CASE 8: Rx medicine with valid prescription → APPROVED
    #
    reasoning = (
        f"Medicine '{name}': stock={stock}, qty={qty}, "
        f"rx_required={med.rx_required}, prescription={'uploaded' if rx_file else 'not needed'}. "
        f"All 5 safety rules passed. DECISION: APPROVED."
    )
    _langfuse_output({"rule": "all_passed", "status": "APPROVED", "reasoning": reasoning})
    return SafetyCheckResult(
        medicine_id=med.id,
        medicine_name=name,
        status="approved",
        rule="all_checks_passed",
        message=f"{name} — all safety checks passed.",
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_summary(blocks, warnings, approved) -> str:
    """Human-readable summary for chat response."""
    if not blocks and not warnings:
        total = len(approved)
        return f"All {total} medicine{'s' if total != 1 else ''} passed safety checks. Ready to order."

    parts = []
    for b in blocks:
        parts.append(f"⛔ {b['medicine_name']}: {b['message']}")
    for w in warnings:
        parts.append(f"⚠ {w['medicine_name']}: {w['message']}")
    if approved:
        parts.append(f"✅ {len(approved)} medicine{'s' if len(approved) != 1 else ''} approved.")
    return "\n".join(parts)


def _langfuse_output(data: dict):
    """Safely log to Langfuse. Never crashes if Langfuse is unavailable."""
    try:
        langfuse_context.update_current_observation(output=data)
    except Exception:
        pass  # Langfuse is optional — never block the main flow


def _elapsed(start: float) -> int:
    """Milliseconds since start."""
    return int((time.time() - start) * 1000)