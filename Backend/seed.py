"""Seed the database with initial medicine data."""

from database import SessionLocal, Base, engine
from models.medicine import Medicine

Base.metadata.create_all(bind=engine)

MEDICINES = [
    {"name": "Panthenol Spray, 46,3 mg/g", "pzn": "04020784", "price": 16.95, "package": "130 g", "stock": 72, "rx_required": False, "description": "Schaumspray zur Anwendung auf der Haut."},
    {"name": "NORSAN Omega-3 Total", "pzn": "13476520", "price": 27.00, "package": "200 ml", "stock": 47, "rx_required": False, "description": "Fluessiges Omega-3-Oel aus Fisch."},
    {"name": "NORSAN Omega-3 Vegan", "pzn": "13476394", "price": 29.00, "package": "100 ml", "stock": 41, "rx_required": False, "description": "Pflanzliches Omega-3 aus Algen."},
    {"name": "NORSAN Omega-3 Kapseln", "pzn": "13512730", "price": 29.00, "package": "120 st", "stock": 55, "rx_required": False, "description": "Omega-3-Kapseln zur taeglichen Ergaenzung."},
    {"name": "Vividrin iso EDO antiallergische Augentropfen", "pzn": "16507327", "price": 8.28, "package": "30x0.5 ml", "stock": 65, "rx_required": False, "description": "Konservierungsmittelfreie Augentropfen."},
    {"name": "Aqualibra 80 mg/90 mg/180 mg Filmtabletten", "pzn": "00795287", "price": 27.82, "package": "60 st", "stock": 36, "rx_required": False, "description": "Pflanzliches Arzneimittel fuer die Blasenfunktion."},
    {"name": "Vitasprint Pro Energie", "pzn": "14050243", "price": 15.95, "package": "8 st", "stock": 90, "rx_required": False, "description": "B-Vitamine und Aminosaeuren."},
    {"name": "Cystinol akut", "pzn": "07114824", "price": 26.50, "package": "60 st", "stock": 33, "rx_required": False, "description": "Zur Behandlung akuter Harnwegsinfektionen."},
    {"name": "Cromo-ratiopharm Augentropfen Einzeldosis", "pzn": "04884527", "price": 7.59, "package": "20x0.5 ml", "stock": 57, "rx_required": False, "description": "Antiallergische Augentropfen."},
    {"name": "Kijimea Reizdarm PRO", "pzn": "15999676", "price": 38.99, "package": "28 st", "stock": 29, "rx_required": False, "description": "Linderung von Reizdarmsymptomen."},
    {"name": "Mucosolvan 1 mal taeglich Retardkapseln", "pzn": "15210915", "price": 39.97, "package": "50 st", "stock": 24, "rx_required": True, "description": "Langwirksames Arzneimittel zur Schleimloesung."},
    {"name": "OMNi-BiOTiC SR-9 mit B-Vitaminen", "pzn": "16487346", "price": 44.50, "package": "28x3 g", "stock": 20, "rx_required": False, "description": "Probiotikum zur Unterstuetzung der Darmflora."},
    {"name": "Osa Schorf Spray", "pzn": "16781761", "price": 15.45, "package": "30 ml", "stock": 49, "rx_required": False, "description": "Pflegespray fuer trockene Kopfhaut bei Babys."},
    {"name": "Multivitamin Fruchtgummibaerchen vegan", "pzn": "16908486", "price": 12.74, "package": "60 st", "stock": 120, "rx_required": False, "description": "Vegane Multivitamin-Fruchtgummibaerchen."},
    {"name": "Iberogast Classic", "pzn": "16507540", "price": 28.98, "package": "50 ml", "stock": 42, "rx_required": False, "description": "Pflanzliches Arzneimittel bei Magen-Darm-Beschwerden."},
    {"name": "COLPOFIX", "pzn": "18389398", "price": 49.60, "package": "40 ml", "stock": 18, "rx_required": True, "description": "Vaginalgel zur Unterstuetzung der Cervixgesundheit."},
    {"name": "Augentropfen RedCare", "pzn": "17396686", "price": 12.69, "package": "10 ml", "stock": 70, "rx_required": False, "description": "Befeuchtende Augentropfen bei trockenen Augen."},
    {"name": "MULTILAC Darmsynbiotikum", "pzn": "17931783", "price": 9.99, "package": "10 st", "stock": 92, "rx_required": False, "description": "Kombination aus Pro- und Praebiotika."},
    {"name": "Prostata Men Kapseln", "pzn": "18657640", "price": 19.99, "package": "60 st", "stock": 44, "rx_required": False, "description": "Nahrungsergaenzung fuer Prostatagesundheit."},
    {"name": "Natural Intimate Creme", "pzn": "18769758", "price": 18.90, "package": "50 ml", "stock": 38, "rx_required": False, "description": "Pflegecreme fuer den Intimbereich."},
    {"name": "proBIO 6 Probiotik Kapseln APOMIA", "pzn": "18317737", "price": 34.90, "package": "30 st", "stock": 26, "rx_required": False, "description": "Probiotische Kapseln fuer gesunde Darmflora."},
    {"name": "Eucerin DERMOPURE Triple Effect Reinigungsgel", "pzn": "18222095", "price": 17.25, "package": "150 ml", "stock": 31, "rx_required": False, "description": "Reinigungsgel fuer unreine Haut."},
    {"name": "frida baby FlakeFixer", "pzn": "19140755", "price": 1.00, "package": "1 st", "stock": 64, "rx_required": False, "description": "Sanfte Pflege zur Entfernung von Milchschorf."},
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
