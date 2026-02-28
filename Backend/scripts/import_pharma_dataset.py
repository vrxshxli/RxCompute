"""
Import pharma catalog + consumer order history dataset.

Usage:
  python Backend/scripts/import_pharma_dataset.py
"""

from __future__ import annotations

from datetime import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import SessionLocal
from models.medicine import Medicine
from models.order import Order, OrderItem, OrderStatus
from models.user import User


CATALOG = [
    ("04020784", "Panthenol Spray, 46,3 mg/g Schaum zur Anwendung auf der Haut", 16.95, "130 g", "Schaumspray zur Anwendung auf der Haut. Foerdert die Regeneration gereizter oder geschaedigter Haut und spendet Feuchtigkeit."),
    ("13476520", "NORSAN Omega-3 Total", 27.0, "200 ml", "Fluessiges Omega-3-Oel aus Fisch. Unterstuetzt Herz, Gehirn und Gelenke."),
    ("13476394", "NORSAN Omega-3 Vegan", 29.0, "100 ml", "Pflanzliches Omega-3 aus Algen. Geeignet fuer Vegetarier und Veganer."),
    ("13512730", "NORSAN Omega-3 Kapseln", 29.0, "120 st", "Omega-3-Kapseln zur taeglichen Nahrungsergaenzung."),
    ("16507327", "Vividrin iso EDO antiallergische Augentropfen", 8.28, "30x0.5 ml", "Konservierungsmittelfreie Augentropfen zur Linderung allergischer Beschwerden."),
    ("00795287", "Aqualibra 80 mg/90 mg/180 mg Filmtabletten", 27.82, "60 st", "Pflanzliches Arzneimittel zur Unterstuetzung der Blasenfunktion."),
    ("15210915", "Mucosolvan 1 mal taeglich Retardkapseln", 39.97, "50 st", "Langwirksames Arzneimittel zur Schleimloesung bei Husten."),
    ("18389398", "COLPOFIX", 49.6, "40 ml", "Vaginalgel zur Unterstuetzung der Gesundheit der Zervixschleimhaut."),
    ("00676714", "Livocab direkt Augentropfen 0,05%", 14.99, "4 ml", "Schnell wirksame Augentropfen bei allergischen Augenbeschwerden."),
    ("00766794", "Ramipril - 1 A Pharma 10 mg Tabletten", 12.59, "20 st", "Verschreibungspflichtiges Arzneimittel zur Behandlung von Bluthochdruck."),
    ("10391763", "Minoxidil BIO-H-TIN-Pharma 20 mg/ml Spray", 22.5, "60 ml", "Loesung zur Anwendung auf der Kopfhaut bei erblich bedingtem Haarausfall."),
    ("16815862", "femiLoges 4 mg magensaftresistente Tabletten", 20.44, "30 st", "Hormonfreies Arzneimittel zur Linderung von Wechseljahresbeschwerden."),
    ("18188323", "Paracetamol apodiscounter 500 mg Tabletten", 2.06, "20 st", "Schmerz- und fiebersenkendes Arzneimittel."),
    ("18222095", "Eucerin DERMOPURE Triple Effect Reinigungsgel", 17.25, "150 ml", "Reinigungsgel fuer unreine Haut, reduziert Unreinheiten."),
]


ORDER_HISTORY = [
    ("PAT004", 55, "M", "2024-03-13", "15210915", 1, 39.97, "Once daily", True),
    ("PAT006", 71, "M", "2024-03-09", "00766794", 2, 25.18, "Once daily", True),
    ("PAT008", 42, "M", "2024-03-08", "10391763", 1, 22.50, "Twice daily", True),
    ("PAT016", 53, "F", "2024-02-24", "16815862", 1, 20.44, "Once daily", True),
    ("PAT020", 60, "M", "2024-02-19", "18389398", 1, 49.60, "As needed", True),
    ("PAT002", 62, "M", "2024-02-01", "00795287", 1, 27.82, "Twice daily", True),
    ("PAT034", 48, "M", "2024-01-28", "00676714", 1, 14.99, "Twice daily", True),
]


def _is_rx_by_signal(name: str, desc: str, pzn: str) -> bool:
    n = (name or "").lower()
    d = (desc or "").lower()
    if "verschreibungspflicht" in d:
        return True
    rx_tokens = {"mucosolvan", "ramipril", "minoxidil", "femiloges", "colpofix", "aqualibra", "livocab"}
    if any(t in n for t in rx_tokens):
        return True
    if pzn in {"15210915", "00766794", "10391763", "16815862", "18389398", "00795287", "00676714"}:
        return True
    return False


def run_import() -> None:
    db = SessionLocal()
    try:
        med_by_pzn: dict[str, Medicine] = {}
        for pzn, name, price, package, desc in CATALOG:
            row = db.query(Medicine).filter(Medicine.pzn == pzn).first()
            rx_required = _is_rx_by_signal(name, desc, pzn)
            if not row:
                row = Medicine(
                    name=name,
                    pzn=pzn,
                    price=float(price),
                    package=package,
                    stock=120,
                    rx_required=rx_required,
                    description=desc,
                )
                db.add(row)
                db.flush()
            else:
                row.name = name
                row.price = float(price)
                row.package = package
                row.description = desc
                row.rx_required = bool(rx_required or row.rx_required)
                row.stock = max(int(row.stock or 0), 120)
            med_by_pzn[pzn] = row
        db.commit()

        for patient_id, age, gender, date_s, pzn, qty, total, dosage, rx_required in ORDER_HISTORY:
            email = f"{patient_id.lower()}@dataset.local"
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(name=patient_id, age=int(age), gender=gender, email=email, role="user", is_registered=True, is_verified=True)
                db.add(user)
                db.flush()
            else:
                user.age = int(age)
                user.gender = gender
                user.name = patient_id

            med = med_by_pzn.get(pzn) or db.query(Medicine).filter(Medicine.pzn == pzn).first()
            if not med:
                continue
            uid = f"HST-{patient_id}-{date_s.replace('-', '')}-{pzn[-4:]}"
            exists = db.query(Order).filter(Order.order_uid == uid).first()
            if exists:
                continue
            dt = datetime.strptime(date_s, "%Y-%m-%d")
            order = Order(
                order_uid=uid,
                user_id=user.id,
                status=OrderStatus.delivered,
                total=float(total),
                payment_method="online",
                created_at=dt,
                updated_at=dt,
                last_status_updated_at=dt,
            )
            db.add(order)
            db.flush()
            db.add(
                OrderItem(
                    order_id=order.id,
                    medicine_id=med.id,
                    name=med.name,
                    quantity=int(qty),
                    price=float(total) / max(int(qty), 1),
                    dosage_instruction=dosage,
                    strips_count=max(int(qty), 1),
                    rx_required=bool(rx_required),
                )
            )
        db.commit()
        print("Dataset import complete: catalog + history.")
    finally:
        db.close()


if __name__ == "__main__":
    run_import()

