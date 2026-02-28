import json
import os
import re


_BASE_RX_REQUIRED_PZNS = {
    "15210915",  # Mucosolvan
    "00766794",  # Ramipril
    "10391763",  # Minoxidil
    "16815862",  # femiLoges
    "18389398",  # COLPOFIX
    "00795287",  # Aqualibra (dataset-labeled Rx)
    "00676714",  # Livocab (dataset-labeled Rx)
}

_BASE_RX_REQUIRED_NAME_TOKENS = {
    "mucosolvan",
    "ramipril",
    "minoxidil",
    "femiloges",
    "colpofix",
    "aqualibra",
    "livocab",
}

_MODEL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "rx_signal_model.json")
)


def _normalize(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _load_trained_model() -> tuple[set[str], set[str]]:
    pzns = set(_BASE_RX_REQUIRED_PZNS)
    tokens = set(_BASE_RX_REQUIRED_NAME_TOKENS)
    if not os.path.exists(_MODEL_PATH):
        return pzns, tokens
    try:
        with open(_MODEL_PATH, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        for p in payload.get("rx_required_pzns", []):
            pzns.add(str(p).strip())
        for t in payload.get("rx_name_tokens", []):
            t = _normalize(str(t))
            if t:
                tokens.add(t)
    except Exception:
        pass
    return pzns, tokens


_RX_PZNS, _RX_TOKENS = _load_trained_model()


def is_rx_required_from_knowledge(medicine_name: str | None, pzn: str | None, description: str | None = None) -> bool:
    p = str(pzn or "").strip()
    if p and p in _RX_PZNS:
        return True

    n = _normalize(medicine_name)
    d = _normalize(description)
    if "verschreibungspflicht" in d:
        return True
    if not n:
        return False
    return any(tok in n for tok in _RX_TOKENS)

