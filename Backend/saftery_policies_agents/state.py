"""
LangGraph Agent State — the shared "clipboard" that flows between agents.

Each agent reads the fields it needs, does its work, and writes its output
back. The state accumulates results as it moves through the chain.
"""

from typing import TypedDict, Literal, Any, NotRequired


class SafetyCheckResult(TypedDict):
    """One medicine's safety check result."""
    medicine_id: int
    medicine_name: str
    status: Literal["approved", "blocked", "warning"]
    rule: str          # which rule triggered (e.g. "prescription_required")
    message: str       # human-readable explanation
    detail: NotRequired[dict[str, Any]]


class AgentState(TypedDict):
    # ─── Input ──────────────────────────────────────
    user_id: int                       # who is ordering
    user_message: str                  # original chat message

    # ─── Conversation Agent fills these ─────────────
    matched_medicines: list[dict]      # medicines matched from DB
    is_greeting: bool                  # True if user said "hello" etc
    general_response: str              # chat response for greetings

    # ─── Safety Agent fills these ───────────────────
    safety_results: list[SafetyCheckResult]
    has_blocks: bool                   # True = order CANNOT proceed
    has_warnings: bool                 # True = proceed but show warnings
    safety_summary: str                # readable summary

    # ─── Final Response ─────────────────────────────
    response_type: Literal["chat", "medicine_cards", "safety_warning", "error"]
    response_message: str