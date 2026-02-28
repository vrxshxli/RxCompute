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
import os
import mimetypes
import re
import io
import shutil
from datetime import datetime, timezone
from math import ceil
from urllib import request as urllib_request
from langfuse.decorators import observe, langfuse_context
from database import SessionLocal
from models.medicine import Medicine
from models.order import Order, OrderItem, OrderStatus
from saftery_policies_agents.state import AgentState, SafetyCheckResult
from services.rx_knowledge import is_rx_required_from_knowledge

try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover
    pytesseract = None
    Image = None


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
        results = _load_and_check_all(db, state.get("user_id", 0), matched)
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
def _load_and_check_all(db, user_id: int, matched: list[dict]) -> list[SafetyCheckResult]:
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

    ocr_cache: dict[str, dict] = {}
    for item in matched:
        mid = item["medicine_id"]
        qty = item.get("quantity", 1)
        dosage_instruction = item.get("dosage_instruction")
        strips_count = item.get("strips_count")
        rx_file = item.get("prescription_file")
        item_name = item.get("name")
        item_rx_required = bool(item.get("rx_required", False))

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

        ocr_analysis = None
        if med and med.rx_required and rx_file:
            key = str(rx_file).strip()
            if key not in ocr_cache:
                ocr_cache[key] = _verify_prescription_with_gemini_ocr(med.name, key)
            ocr_analysis = ocr_cache[key]

        result = _evaluate_rules(
            db=db,
            user_id=user_id,
            med=med,
            qty=qty,
            strips_count=strips_count,
            dosage_instruction=dosage_instruction,
            rx_file=rx_file,
            item_name=item_name,
            item_rx_required=item_rx_required,
            ocr_analysis=ocr_analysis,
        )
        results.append(result)

    # Cross-medicine interaction checks (pair level).
    pair_alerts = _evaluate_interactions(matched, med_map)
    results.extend(pair_alerts)

    return results


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# INTERNAL: Evaluate all 5 safety rules for one medicine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@observe(name="safety_evaluate_rules")
def _evaluate_rules(
    db,
    user_id: int,
    med: Medicine,
    qty: int,
    strips_count: int | None,
    dosage_instruction: str | None,
    rx_file: str | None,
    item_name: str | None = None,
    item_rx_required: bool = False,
    ocr_analysis: dict | None = None,
) -> SafetyCheckResult:
    """
    Run the 5-rule engine against one medicine.
    Priority order: first BLOCK wins, then first WARNING, then APPROVED.

    Each evaluation is a separate Langfuse span with full reasoning,
    so judges can see exactly why each medicine was approved/blocked.
    """

    stock = med.stock or 0
    name = med.name
    strips = strips_count if (isinstance(strips_count, int) and strips_count > 0) else qty

    # RULE 0: Duplicate active medication order block.
    days_remaining = _active_days_remaining_for_user_medication(db, user_id, med.id)
    if days_remaining is not None and days_remaining > 0:
        reasoning = (
            f"Duplicate order blocked for user_id={user_id}, medicine='{name}'. "
            f"Existing tracked stock has {days_remaining} day(s) remaining."
        )
        _langfuse_output({"rule": "duplicate_active_medication", "status": "BLOCKED", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="blocked",
            rule="duplicate_active_medication",
            message=f"{name} still has approximately {days_remaining} day(s) remaining. Reorder is allowed only after current cycle is finished.",
            detail={"days_remaining": days_remaining},
        )
    if days_remaining is None:
        hist_days_remaining = _estimated_days_remaining_from_latest_delivery_history(db, user_id, med.id, med.package)
        if hist_days_remaining is not None and hist_days_remaining > 0:
            reasoning = (
                f"History-based duplicate order blocked for user_id={user_id}, medicine='{name}'. "
                f"Latest delivered supply indicates about {hist_days_remaining} day(s) remaining."
            )
            _langfuse_output({"rule": "duplicate_from_order_history", "status": "BLOCKED", "reasoning": reasoning})
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="duplicate_from_order_history",
                message=f"{name} appears to still be active from your latest delivered order ({hist_days_remaining} day(s) remaining).",
                detail={"days_remaining": hist_days_remaining},
            )

    # RULE 0b: Same medicine already has active in-flight order.
    inflight = _has_active_inflight_order_for_medicine(db, user_id, med.id)
    if inflight:
        reasoning = (
            f"Duplicate in-flight order blocked for user_id={user_id}, medicine='{name}'. "
            f"Existing active order={inflight.order_uid} status={inflight.status.value if hasattr(inflight.status, 'value') else inflight.status}."
        )
        _langfuse_output({"rule": "duplicate_active_order_inflight", "status": "BLOCKED", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="blocked",
            rule="duplicate_active_order_inflight",
            message=f"{name} already has an active order ({inflight.order_uid}). Please wait until it is delivered or cancelled.",
            detail={
                "existing_order_uid": inflight.order_uid,
                "existing_order_status": inflight.status.value if hasattr(inflight.status, "value") else str(inflight.status),
            },
        )

    # ────────────────────────────────────────────────────
    # RULE 1: Prescription Required
    # ────────────────────────────────────────────────────
    # USE CASE 1: Mucosolvan (rx_required=True), no prescription → BLOCK
    # USE CASE 8: Mucosolvan WITH prescription → PASS (continues to next rules)
    #
    require_rx = (
        bool(med.rx_required)
        or bool(item_rx_required)
        or is_rx_required_from_knowledge(med.name, med.pzn, med.description)
    )
    if require_rx and not rx_file:
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

    # RULE 1b: Prescription file must look valid and clear (extension/path sanity).
    if require_rx and rx_file:
        rx = str(rx_file).strip()
        rx_l = rx.lower()
        allowed_ext = {".jpg", ".jpeg", ".png", ".pdf", ".webp"}
        ext = os.path.splitext(rx_l)[1]
        is_cloudinary = rx_l.startswith("https://res.cloudinary.com/")
        is_local_upload = "/uploads/prescriptions/" in rx_l
        if (ext not in allowed_ext) or (not is_cloudinary and not is_local_upload):
            reasoning = (
                f"Medicine '{name}' requires Rx. Uploaded file '{rx_file}' failed validation "
                f"(expected Cloudinary URL or /uploads/prescriptions path + allowed extension). DECISION: BLOCK."
            )
            _langfuse_output({"rule": "prescription_file_invalid", "status": "BLOCKED", "reasoning": reasoning})
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="prescription_file_invalid",
                message=f"{name}: uploaded prescription is invalid or unclear. Please upload a clear prescription image/PDF.",
            )
        ocr_decision = ocr_analysis or _verify_prescription_with_gemini_ocr(name, rx)
        if not ocr_decision["ok"]:
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="prescription_ocr_rejected",
                message=f"{name}: {ocr_decision['reason']}",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": ocr_decision.get("indicators", {}),
                },
            )
        extracted_text = str(ocr_decision.get("extracted_text", "") or "")
        if not _prescription_mentions_medicine(extracted_text, item_name or name):
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="prescription_medicine_mismatch",
                message=f"{name}: uploaded prescription does not clearly mention this medicine.",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {**ocr_decision.get("indicators", {}), "medicine_name_found": False},
                },
            )

        strength = _extract_strength_token(item_name or name)
        if strength and _normalize_text(strength) not in _normalize_text(extracted_text):
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="prescription_dosage_strength_mismatch",
                message=f"{name}: strength/dosage on prescription does not match ordered medicine ({strength}).",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {**ocr_decision.get("indicators", {}), "strength_found": False},
                },
            )

        dosage_txt = (dosage_instruction or "").strip()
        if not dosage_txt:
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="dosage_missing_for_rx",
                message=f"{name}: dosage instruction is required for Rx verification.",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {**ocr_decision.get("indicators", {}), "dosage_found": False},
                },
            )
        if not _prescription_mentions_dosage(extracted_text, dosage_txt):
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="prescription_dosage_instruction_mismatch",
                message=f"{name}: dosage instruction '{dosage_txt}' not found in prescription text.",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {**ocr_decision.get("indicators", {}), "dosage_found": False},
                },
            )

        strips_to_check = strips_count if isinstance(strips_count, int) and strips_count > 0 else qty
        if strips_to_check >= 1 and not _prescription_mentions_strips(extracted_text, strips_to_check):
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="prescription_strips_mismatch",
                message=f"{name}: requested strips/quantity ({strips_to_check}) not present in prescription.",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {**ocr_decision.get("indicators", {}), "strips_found": False},
                },
            )

        if not _prescription_mentions_days(extracted_text):
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="prescription_days_missing",
                message=f"{name}: prescription does not clearly mention treatment days/duration.",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {**ocr_decision.get("indicators", {}), "days_found": False},
                },
            )
        days = _extract_prescribed_days(extracted_text)
        per_day = _estimate_daily_units_from_dosage(dosage_txt)
        if days is None or days <= 0:
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="prescription_days_parse_failed",
                message=f"{name}: unable to parse treatment duration from prescription.",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {**ocr_decision.get("indicators", {}), "days_found": False},
                },
            )
        if per_day is None or per_day <= 0:
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="dosage_parse_failed",
                message=f"{name}: dosage format is unclear; cannot compute daily consumption.",
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {**ocr_decision.get("indicators", {}), "dosage_found": False},
                },
            )
        units_per_strip = _extract_units_per_strip(med.package)
        required_units = days * per_day
        required_strips = max(1, ceil(required_units / units_per_strip))
        if strips_to_check < required_strips:
            return SafetyCheckResult(
                medicine_id=med.id,
                medicine_name=name,
                status="blocked",
                rule="insufficient_strips_for_duration",
                message=(
                    f"{name}: requested strips ({strips_to_check}) are insufficient for {days} day(s) at "
                    f"{per_day}/day. Minimum required strips: {required_strips}."
                ),
                detail={
                    "confidence": ocr_decision.get("confidence"),
                    "indicators": {
                        **ocr_decision.get("indicators", {}),
                        "days_found": True,
                        "dosage_found": True,
                        "required_strips": required_strips,
                    },
                },
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

    # RULE 3b: Strips must be positive and not exceed safe pack threshold.
    if strips <= 0:
        reasoning = (
            f"Medicine '{name}' has strips_count={strips}. "
            f"Strips must be >=1. DECISION: BLOCK."
        )
        _langfuse_output({"rule": "invalid_strips", "status": "BLOCKED", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="blocked",
            rule="invalid_strips",
            message=f"{name}: invalid strips requested. Minimum 1 strip is required.",
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
    if qty > 5 or strips > 10:
        reasoning = (
            f"Medicine '{name}' ordered in quantity={qty}, strips={strips} "
            f"(above unusual threshold). "
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

    # RULE 6: Dosage quality check (minimum meaningful instruction for safe dispense).
    dosage_txt = (dosage_instruction or "").strip()
    if len(dosage_txt) < 4:
        reasoning = (
            f"Medicine '{name}' has weak dosage instruction '{dosage_instruction}'. "
            f"DECISION: WARNING — requires pharmacist review before final dispense."
        )
        _langfuse_output({"rule": "dosage_instruction_weak", "status": "WARNING", "reasoning": reasoning})
        return SafetyCheckResult(
            medicine_id=med.id,
            medicine_name=name,
            status="warning",
            rule="dosage_instruction_weak",
            message=f"{name}: dosage instruction is incomplete. Pharmacist review recommended.",
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


@observe(name="safety_interaction_rules")
def _evaluate_interactions(matched: list[dict], med_map: dict[int, Medicine]) -> list[SafetyCheckResult]:
    results: list[SafetyCheckResult] = []
    ids = [m.get("medicine_id") for m in matched if m.get("medicine_id") in med_map]
    unique_ids = list(dict.fromkeys(ids))
    if len(unique_ids) < 2:
        return results

    names = {mid: (med_map[mid].name or "").lower() for mid in unique_ids}
    severe_pairs = [
        ("warfarin", "ibuprofen"),
        ("sildenafil", "nitrate"),
    ]
    for i in range(len(unique_ids)):
        for j in range(i + 1, len(unique_ids)):
            a_id, b_id = unique_ids[i], unique_ids[j]
            a_name, b_name = names[a_id], names[b_id]
            for x, y in severe_pairs:
                if ((x in a_name and y in b_name) or (x in b_name and y in a_name)):
                    msg = (
                        f"Potential severe interaction: '{med_map[a_id].name}' + '{med_map[b_id].name}'. "
                        f"Pharmacist/manual review required before order."
                    )
                    _langfuse_output({"rule": "medicine_interaction_severe", "status": "BLOCKED", "pair": [a_id, b_id], "message": msg})
                    results.append(
                        SafetyCheckResult(
                            medicine_id=a_id,
                            medicine_name=f"{med_map[a_id].name} + {med_map[b_id].name}",
                            status="blocked",
                            rule="medicine_interaction_severe",
                            message=msg,
                        )
                    )
    if not results and len(unique_ids) >= 2:
        # Generic pair review warning when multiple medicines are ordered together.
        first = unique_ids[0]
        second = unique_ids[1]
        msg = (
            f"Combination review: '{med_map[first].name}' + '{med_map[second].name}' "
            f"ordered together. Interaction check passed but pharmacist review recommended."
        )
        _langfuse_output({"rule": "medicine_interaction_review", "status": "WARNING", "pair": [first, second], "message": msg})
        results.append(
            SafetyCheckResult(
                medicine_id=first,
                medicine_name=f"{med_map[first].name} + {med_map[second].name}",
                status="warning",
                rule="medicine_interaction_review",
                message=msg,
            )
        )
    return results


@observe(name="safety_prescription_ocr")
def _verify_prescription_with_gemini_ocr(medicine_name: str, rx_file: str) -> dict:
    """
    Tesseract OCR-based strict check:
      - image must contain enough readable prescription text
      - no inferred/hallucinated details allowed
    """
    del medicine_name
    if pytesseract is None or Image is None:
        return {
            "ok": False,
            "reason": "Tesseract OCR package is unavailable on server.",
            "confidence": 0.0,
            "indicators": {},
        }
    if shutil.which("tesseract") is None:
        return {
            "ok": False,
            "reason": "Tesseract binary is not installed on server.",
            "confidence": 0.0,
            "indicators": {},
        }

    try:
        file_bytes, mime_type = _load_prescription_bytes(rx_file)
    except Exception as exc:
        return {"ok": False, "reason": f"Unable to open prescription file for AI verification: {exc}", "confidence": 0.0, "indicators": {}}
    try:
        extracted_text, ocr_conf = _extract_text_with_tesseract(file_bytes, mime_type)
    except Exception as exc:
        return {
            "ok": False,
            "reason": f"OCR extraction failed: {exc}",
            "confidence": 0.0,
            "indicators": {},
            "extracted_text": "",
        }

    text_norm = _normalize_text(extracted_text)
    rx_markers = {"rx", "prescription", "doctor", "patient", "clinic", "hospital"}
    marker_hits = sum(1 for k in rx_markers if k in text_norm)
    is_prescription = marker_hits >= 2
    dosage_like = bool(re.search(r"\b\d+\s*-\s*\d+\s*-\s*\d+\b", extracted_text)) or any(
        w in text_norm for w in {"od", "bd", "tid", "qid", "daily", "day", "days"}
    )
    medicine_or_dosage_present = dosage_like or bool(re.search(r"\b\d+\s?(mg|mcg|ml|g)\b", text_norm))
    is_clear = len(text_norm) >= 40 and len(re.findall(r"[a-zA-Z]{3,}", extracted_text)) >= 6
    doctor_present = any(k in text_norm for k in {"doctor", "dr", "clinic", "hospital", "mbbs"})
    confidence = _estimate_ocr_confidence(text_norm, is_prescription, dosage_like, doctor_present, ocr_conf)
    reason = "Prescription OCR validation failed"

    _langfuse_output(
        {
            "rule": "prescription_ocr_check",
            "is_prescription": is_prescription,
            "is_clear": is_clear,
            "doctor_present": doctor_present,
            "medicine_or_dosage_present": medicine_or_dosage_present,
            "extracted_text_length": len(extracted_text),
            "ocr_confidence": ocr_conf,
            "confidence": confidence,
            "reason": reason,
        }
    )
    text_ok = len(extracted_text) >= 30 and _looks_like_medical_text(extracted_text) and ocr_conf >= 40.0
    passed = is_prescription and is_clear and doctor_present and medicine_or_dosage_present and confidence >= 0.65
    indicators = {
        "is_prescription": is_prescription,
        "is_clear": is_clear,
        "doctor_present": doctor_present,
        "medicine_or_dosage_present": medicine_or_dosage_present,
        "text_detected": text_ok,
        "ocr_confidence": ocr_conf,
        "marker_hits": marker_hits,
    }
    if not passed or not text_ok:
        return {
            "ok": False,
            "reason": reason or ("Prescription text is not clear/readable." if not text_ok else "Prescription is unclear or not valid."),
            "confidence": confidence,
            "indicators": indicators,
            "extracted_text": extracted_text,
        }
    return {
        "ok": True,
        "reason": "Prescription verified by OCR",
        "confidence": confidence,
        "indicators": indicators,
        "extracted_text": extracted_text,
    }


def _extract_text_with_tesseract(file_bytes: bytes, mime_type: str) -> tuple[str, float]:
    mt = (mime_type or "").lower()
    if "pdf" in mt:
        raise RuntimeError("PDF OCR is not enabled with tesseract-only mode. Upload image prescription.")
    image = Image.open(io.BytesIO(file_bytes))
    if image.mode not in {"RGB", "L"}:
        image = image.convert("RGB")
    text = pytesseract.image_to_string(image, config="--oem 3 --psm 6").strip()
    conf = _average_ocr_confidence(image)
    return text, conf


def _estimate_ocr_confidence(text_norm: str, is_prescription: bool, dosage_like: bool, doctor_present: bool, ocr_conf: float) -> float:
    score = 0.25
    if len(text_norm) >= 50:
        score += 0.2
    if is_prescription:
        score += 0.2
    if dosage_like:
        score += 0.2
    if doctor_present:
        score += 0.15
    if ocr_conf >= 50:
        score += 0.15
    return min(score, 0.95)


def _average_ocr_confidence(image) -> float:
    try:
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confs = []
        for raw in data.get("conf", []):
            try:
                v = float(raw)
            except Exception:
                continue
            if v >= 0:
                confs.append(v)
        if not confs:
            return 0.0
        return sum(confs) / len(confs)
    except Exception:
        return 0.0


def _load_prescription_bytes(rx_file: str) -> tuple[bytes, str]:
    rx = str(rx_file).strip()
    if rx.lower().startswith("http://") or rx.lower().startswith("https://"):
        with urllib_request.urlopen(rx, timeout=12) as resp:
            content = resp.read()
            content_type = resp.headers.get("Content-Type", "") or ""
        mime_type = content_type.split(";")[0].strip() or _guess_mime(rx)
        return content, mime_type

    if rx.startswith("/uploads/prescriptions/"):
        uploads_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
        local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", rx.lstrip("/")))
        if not local_path.startswith(uploads_root):
            raise RuntimeError("invalid local prescription path")
        with open(local_path, "rb") as fh:
            content = fh.read()
        return content, _guess_mime(local_path)
    raise RuntimeError("unsupported prescription path")


def _guess_mime(path: str) -> str:
    guessed, _ = mimetypes.guess_type(path)
    return guessed or "application/octet-stream"


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _has_digit(text: str) -> bool:
    return bool(re.search(r"\d", text or ""))


def _extract_strength_token(name: str) -> str:
    m = re.search(r"\b\d+\s?(mg|mcg|ml|g)\b", (name or "").lower())
    return m.group(0) if m else ""


def _looks_like_medical_text(text: str) -> bool:
    t = _normalize_text(text)
    keywords = {"rx", "prescription", "tab", "tablet", "capsule", "mg", "ml", "doctor", "dose", "daily"}
    return any(k in t for k in keywords)


def _prescription_mentions_medicine(text: str, medicine_name: str) -> bool:
    t = _normalize_text(text)
    name_tokens = [tok for tok in _normalize_text(medicine_name).split() if len(tok) >= 4 and tok not in {"tablet", "tablets", "capsule", "capsules"}]
    if not name_tokens:
        return False
    # Require at least one strong token and preferably first brand token.
    first = name_tokens[0]
    if first not in t:
        return False
    hit_count = sum(1 for tok in name_tokens if tok in t)
    if len(name_tokens) >= 2:
        return hit_count >= 2
    return hit_count >= 1


def _prescription_mentions_dosage(text: str, dosage_instruction: str) -> bool:
    t = _normalize_text(text)
    d = _normalize_text(dosage_instruction)
    if not d:
        return False
    # Ambiguous bare number like "2" is not an acceptable dosage instruction.
    if re.fullmatch(r"\d+", d):
        return False
    if d in t:
        return True
    # Accept numeric schedule presence (e.g. 1-0-1, 1 0 1).
    nums = re.findall(r"\d+", dosage_instruction or "")
    if nums and " ".join(nums) in t:
        return True
    tokens = [x for x in d.split() if len(x) >= 3]
    return any(tok in t for tok in tokens)


def _prescription_mentions_strips(text: str, strips: int) -> bool:
    t = _normalize_text(text)
    patterns = [
        f"{strips} strip",
        f"{strips} strips",
        f"{strips} tab",
        f"{strips} tablet",
        f"{strips} tablets",
    ]
    return any(p in t for p in patterns)


def _prescription_mentions_days(text: str) -> bool:
    t = _normalize_text(text)
    if re.search(r"\b\d+\s*(day|days|week|weeks|month|months)\b", t):
        return True
    # Also accept compact forms such as "x5d", "5d", "7days".
    return bool(re.search(r"\b(x?\d+\s*d)\b", t))


def _extract_prescribed_days(text: str) -> int | None:
    t = _normalize_text(text)
    m = re.search(r"\b(\d+)\s*(day|days)\b", t)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(\d+)\s*(week|weeks)\b", t)
    if m:
        return int(m.group(1)) * 7
    m = re.search(r"\b(\d+)\s*(month|months)\b", t)
    if m:
        return int(m.group(1)) * 30
    m = re.search(r"\bx?(\d+)\s*d\b", t)
    if m:
        return int(m.group(1))
    return None


def _estimate_daily_units_from_dosage(dosage_instruction: str) -> int | None:
    d = _normalize_text(dosage_instruction)
    nums = [int(x) for x in re.findall(r"\d+", d)]
    if "-" in dosage_instruction and nums:
        s = sum(nums[:4])
        return s if s > 0 else None
    if len(nums) >= 2 and ("per day" in d or "/day" in d):
        return nums[0] if nums[0] > 0 else None
    if len(nums) == 1 and ("daily" in d or "day" in d):
        return nums[0] if nums[0] > 0 else None
    if "once daily" in d or "od" in d:
        return 1
    if "twice daily" in d or "bd" in d:
        return 2
    if "thrice daily" in d or "tid" in d:
        return 3
    # Do not infer from a single bare number without clear schedule context.
    return None


def _extract_units_per_strip(package: str | None) -> int:
    p = (package or "").lower()
    m = re.search(r"\b(\d+)\s*(tablet|tablets|capsule|capsules|tab)\b", p)
    if m:
        return max(int(m.group(1)), 1)
    return 20


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


def _active_days_remaining_for_user_medication(db, user_id: int, medicine_id: int) -> int | None:
    if not user_id or not medicine_id:
        return None
    from models.user_medication import UserMedication

    row = (
        db.query(UserMedication)
        .filter(UserMedication.user_id == user_id, UserMedication.medicine_id == medicine_id)
        .order_by(UserMedication.created_at.desc())
        .first()
    )
    if not row:
        return None
    now = datetime.now(timezone.utc)
    created = row.created_at or now
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    elapsed_days = max((now - created).days, 0)
    freq = max(int(row.frequency_per_day or 1), 1)
    qty = max(int(row.quantity_units or 0), 0)
    remaining_units = max(qty - (elapsed_days * freq), 0)
    if remaining_units <= 0:
        return 0
    return int(ceil(remaining_units / freq))


def _has_active_inflight_order_for_medicine(db, user_id: int, medicine_id: int) -> Order | None:
    if not user_id or not medicine_id:
        return None
    active_statuses = [
        OrderStatus.pending,
        OrderStatus.confirmed,
        OrderStatus.verified,
        OrderStatus.picking,
        OrderStatus.packed,
        OrderStatus.dispatched,
    ]
    return (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            Order.user_id == user_id,
            OrderItem.medicine_id == medicine_id,
            Order.status.in_(active_statuses),
        )
        .order_by(Order.created_at.desc())
        .first()
    )


def _estimated_days_remaining_from_latest_delivery_history(
    db,
    user_id: int,
    medicine_id: int,
    package: str | None,
) -> int | None:
    if not user_id or not medicine_id:
        return None
    # Use latest delivered order line when tracking row is missing.
    row = (
        db.query(Order, OrderItem)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            Order.user_id == user_id,
            OrderItem.medicine_id == medicine_id,
            Order.status == OrderStatus.delivered,
        )
        .order_by(Order.last_status_updated_at.desc(), Order.updated_at.desc(), Order.created_at.desc())
        .first()
    )
    if not row:
        return None
    order, item = row
    delivered_at = order.last_status_updated_at or order.updated_at or order.created_at
    if not delivered_at:
        return None
    delivered_at = delivered_at if delivered_at.tzinfo else delivered_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    elapsed_days = max((now - delivered_at).days, 0)

    dosage_txt = (item.dosage_instruction or "").lower()
    freq = 1
    tri = re.search(r"\b(\d+)\s*-\s*(\d+)\s*-\s*(\d+)\b", dosage_txt)
    if tri:
        freq = max(int(tri.group(1)) + int(tri.group(2)) + int(tri.group(3)), 1)
    else:
        xday = re.search(r"\b(\d+)\s*(x|times?)\s*(/|per)?\s*day\b", dosage_txt)
        if xday:
            freq = max(int(xday.group(1)), 1)
        elif "twice" in dosage_txt or "bd" in dosage_txt:
            freq = 2
        elif "thrice" in dosage_txt or "tid" in dosage_txt:
            freq = 3

    units_per_pack = _extract_units_per_strip(package)
    packs = max(int(item.strips_count or item.quantity or 1), 1)
    supplied_units = max(packs * units_per_pack, packs)
    remaining_units = max(supplied_units - (elapsed_days * freq), 0)
    if remaining_units <= 0:
        return 0
    return int(ceil(remaining_units / freq))


def _langfuse_output(data: dict):
    """Safely log to Langfuse. Never crashes if Langfuse is unavailable."""
    try:
        langfuse_context.update_current_observation(output=data)
    except Exception:
        pass  # Langfuse is optional — never block the main flow


def _elapsed(start: float) -> int:
    """Milliseconds since start."""
    return int((time.time() - start) * 1000)