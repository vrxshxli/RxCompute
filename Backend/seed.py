"""Seed the database with initial medicine data."""

from database import SessionLocal, Base, engine
from models.medicine import Medicine

Base.metadata.create_all(bind=engine)

MEDICINES = [
    {"name": "NORSAN Omega-3 Total", "pzn": "13476520", "price": 27.00, "package": "200 ml", "stock": 47, "rx_required": False},
    {"name": "Paracetamol 500mg", "pzn": "03295091", "price": 4.50, "package": "20 st", "stock": 156, "rx_required": False},
    {"name": "Panthenol Spray, 46,3 mg/g", "pzn": "04020784", "price": 8.90, "package": "130 g", "stock": 23, "rx_required": False},
    {"name": "Mucosolvan Capsules 75mg", "pzn": "11162860", "price": 12.50, "package": "50 st", "stock": 34, "rx_required": True},
    {"name": "Ibuprofen 400mg", "pzn": "02188645", "price": 5.20, "package": "50 st", "stock": 89, "rx_required": False},
    {"name": "Vitamin D3 1000 IU", "pzn": "08451902", "price": 9.50, "package": "60 st", "stock": 135, "rx_required": False},
]


def seed():
    db = SessionLocal()
    try:
        existing = db.query(Medicine).count()
        if existing > 0:
            print(f"Database already has {existing} medicines — skipping seed.")
            return

        for m in MEDICINES:
            db.add(Medicine(**m))
        db.commit()
        print(f"Seeded {len(MEDICINES)} medicines.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
