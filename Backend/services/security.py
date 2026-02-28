import hashlib
import hmac
import os
import re


_RAG_SECURITY_POLICIES = [
    "DB writes are allowed only through ORM models. Never execute raw SQL from user text.",
    "Roles allowed to create patient orders: user, admin, pharmacy_store.",
    "Roles allowed for autonomous order execution: user, admin, pharmacy_store.",
    "Prediction refill confirmation may execute only for authenticated actor and validated target user.",
    "Free-text inputs must be scanned for SQL/meta-command tokens before any DB mutation.",
    "Unauthorized role access must fail closed with explicit denial.",
]

_ALLOWED_ACTION_ROLES = {
    "create_order": {"user", "admin", "pharmacy_store"},
    "order_agent_execute": {"user", "admin", "pharmacy_store"},
    "prediction_refill_confirm": {"user", "admin", "pharmacy_store"},
}

_SQL_INJECTION_PATTERN = re.compile(
    r"(;|--|/\*|\*/|\bdrop\b|\btruncate\b|\balter\b|\bunion\b\s+\bselect\b)",
    flags=re.IGNORECASE,
)


def hash_password(password: str, iterations: int = 120_000) -> str:
    salt = os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${dk.hex()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        algo, iter_s, salt, digest = password_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iter_s),
        )
        return hmac.compare_digest(dk.hex(), digest)
    except Exception:
        return False


def retrieve_security_context(query: str, top_k: int = 3) -> list[str]:
    """
    Lightweight RAG retrieval for DB security policies.
    Returns top policy snippets most relevant to the current action context.
    """
    q_tokens = {t for t in re.findall(r"[a-z0-9_]+", (query or "").lower()) if len(t) > 1}
    scored = []
    for policy in _RAG_SECURITY_POLICIES:
        p_tokens = {t for t in re.findall(r"[a-z0-9_]+", policy.lower()) if len(t) > 1}
        overlap = len(q_tokens & p_tokens)
        scored.append((overlap, policy))
    ranked = [p for score, p in sorted(scored, key=lambda x: x[0], reverse=True) if score > 0]
    if ranked:
        return ranked[:top_k]
    return _RAG_SECURITY_POLICIES[:top_k]


def enforce_rag_db_guard(
    *,
    actor_role: str,
    action: str,
    free_text_fields: list[str] | None = None,
) -> dict:
    """
    Security gate backed by retrieval of policy snippets (RAG-style context).
    """
    role = (actor_role or "").strip().lower()
    allowed = _ALLOWED_ACTION_ROLES.get(action, set())
    context = retrieve_security_context(f"{role} {action}")
    if allowed and role not in allowed:
        raise PermissionError(f"Role '{role}' is not allowed for action '{action}'")

    for txt in free_text_fields or []:
        if not txt:
            continue
        if _SQL_INJECTION_PATTERN.search(str(txt)):
            raise ValueError("Potentially unsafe query text detected")
    return {"approved": True, "policy_context": context}
