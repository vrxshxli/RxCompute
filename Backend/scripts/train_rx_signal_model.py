"""
Train lightweight Rx signal model from medicines table.

Writes: Backend/data/rx_signal_model.json

Usage:
  python Backend/scripts/train_rx_signal_model.py
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import SessionLocal
from models.medicine import Medicine


def _tokens(name: str) -> list[str]:
    raw = re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()
    return [t for t in raw.split() if len(t) >= 5 and not t.isdigit()]


def train() -> None:
    db = SessionLocal()
    try:
        meds = db.query(Medicine).all()
        rx_pzns = set()
        rx_tokens = set()
        for m in meds:
            if bool(m.rx_required):
                if m.pzn:
                    rx_pzns.add(str(m.pzn).strip())
                for t in _tokens(m.name or ""):
                    rx_tokens.add(t)
        payload = {
            "rx_required_pzns": sorted(rx_pzns),
            "rx_name_tokens": sorted(rx_tokens),
            "medicine_count": len(meds),
            "rx_count": len(rx_pzns),
        }
        out_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "data", "rx_signal_model.json")
        )
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=True, indent=2)
        print(f"Trained Rx signal model written: {out_path}")
    finally:
        db.close()


if __name__ == "__main__":
    train()

