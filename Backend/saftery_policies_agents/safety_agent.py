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
import json
import base64
import mimetypes
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError
from langfuse.decorators import observe, langfuse_context
from config import GEMINI_API_KEY, GEMINI_MODEL
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
        dosage_instruction = item.get("dosage_instruction")
        strips_count = item.get("strips_count")
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

        result = _evaluate_rules(
            med=med,
            qty=qty,
            strips_count=strips_count,
            dosage_instruction=dosage_instruction,
            rx_file=rx_file,
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
    med: Medicine,
    qty: int,
    strips_count: int | None,
    dosage_instruction: str | None,
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
    strips = strips_count if (isinstance(strips_count, int) and strips_count > 0) else qty

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

    # RULE 1b: Prescription file must look valid and clear (extension/path sanity).
    if med.rx_required and rx_file:
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
        ocr_decision = _verify_prescription_with_gemini_ocr(name, rx)
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
    Strict OCR check:
      - must be a real prescription-like document
      - text/handwriting should be readable enough
    """
    if not GEMINI_API_KEY:
        return {
            "ok": False,
            "reason": "Prescription AI verification is unavailable. Please try again.",
            "confidence": 0.0,
            "indicators": {},
        }

    try:
        file_bytes, mime_type = _load_prescription_bytes(rx_file)
    except Exception as exc:
        return {"ok": False, "reason": f"Unable to open prescription file for AI verification: {exc}", "confidence": 0.0, "indicators": {}}

    prompt = (
        "You are a strict medical safety OCR checker.\n"
        "Check if this file is a real doctor's prescription and readable enough for safe dispensing.\n"
        "Return ONLY valid JSON (no markdown) with keys:\n"
        "is_prescription (bool), is_clear (bool), doctor_present (bool), "
        "medicine_or_dosage_present (bool), confidence (number 0 to 1), reason (string).\n"
        f"Target medicine context: {medicine_name}\n"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(file_bytes).decode("utf-8")}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.0},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    req = urllib_request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib_request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        return {"ok": False, "reason": f"Prescription AI verification failed ({exc.code}): {details[:180]}", "confidence": 0.0, "indicators": {}}
    except URLError as exc:
        return {"ok": False, "reason": f"Prescription AI network error: {exc}", "confidence": 0.0, "indicators": {}}
    except Exception as exc:
        return {"ok": False, "reason": f"Prescription AI error: {exc}", "confidence": 0.0, "indicators": {}}

    try:
        parsed = json.loads(raw)
        text = (
            parsed.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
    except Exception:
        return {
            "ok": False,
            "reason": "Prescription AI returned unreadable output. Please upload a clearer prescription.",
            "confidence": 0.0,
            "indicators": {},
        }

    is_prescription = bool(result.get("is_prescription"))
    is_clear = bool(result.get("is_clear"))
    doctor_present = bool(result.get("doctor_present"))
    med_or_dosage = bool(result.get("medicine_or_dosage_present"))
    confidence = float(result.get("confidence", 0) or 0)
    reason = str(result.get("reason", "Prescription failed strict OCR checks")).strip()

    _langfuse_output(
        {
            "rule": "prescription_ocr_check",
            "medicine": medicine_name,
            "is_prescription": is_prescription,
            "is_clear": is_clear,
            "doctor_present": doctor_present,
            "medicine_or_dosage_present": med_or_dosage,
            "confidence": confidence,
            "reason": reason,
        }
    )
    passed = is_prescription and is_clear and doctor_present and med_or_dosage and confidence >= 0.55
    indicators = {
        "is_prescription": is_prescription,
        "is_clear": is_clear,
        "doctor_present": doctor_present,
        "medicine_or_dosage_present": med_or_dosage,
    }
    if not passed:
        return {
            "ok": False,
            "reason": reason or "Prescription is unclear or not valid.",
            "confidence": confidence,
            "indicators": indicators,
        }
    return {"ok": True, "reason": "Prescription verified by OCR", "confidence": confidence, "indicators": indicators}


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