"""
Simple migration script — adds missing columns to existing tables.
Safe to run multiple times (checks before altering).
"""

from sqlalchemy import text, inspect
from database import engine, Base
from database import SessionLocal

# Import all models so Base.metadata knows about them
from models.user import User, OTP  # noqa: F401
from models.medicine import Medicine  # noqa: F401
from models.order import Order, OrderItem  # noqa: F401
from models.notification import Notification  # noqa: F401
from models.user_medication import UserMedication  # noqa: F401
from models.webhook_log import WebhookLog  # noqa: F401
from models.pharmacy_store import PharmacyStore  # noqa: F401
from models.warehouse import WarehouseStock, WarehouseTransfer, PharmacyStock  # noqa: F401
from services.security import hash_password


def get_existing_columns(conn, table_name: str) -> set:
    """Get the set of column names that already exist in a table."""
    insp = inspect(conn)
    if not insp.has_table(table_name):
        return set()
    return {col["name"] for col in insp.get_columns(table_name)}


def migrate():
    with engine.connect() as conn:
        lock_acquired = False
        try:
            # Prevent concurrent migration execution across multiple startup workers.
            lock_row = conn.execute(text("SELECT pg_try_advisory_lock(987654321)")).scalar()
            lock_acquired = bool(lock_row)
        except Exception:
            # Non-Postgres environments may not support advisory locks.
            lock_acquired = True
        if not lock_acquired:
            print("  · Migration skipped: another process is running migrations")
            return

        try:
        # 1. Create any tables that don't exist yet
            Base.metadata.create_all(bind=engine)
            print("  ✓ Tables created/verified")

            # 2. Add missing columns to 'users' table
            existing = get_existing_columns(conn, "users")
            print(f"  ℹ Existing columns in users: {existing}")

            migrations = [
                ("google_id", "VARCHAR(255) UNIQUE"),
                ("profile_picture", "TEXT"),
                ("push_token", "VARCHAR(255)"),
                ("location_text", "VARCHAR(255)"),
                ("location_lat", "DOUBLE PRECISION"),
                ("location_lng", "DOUBLE PRECISION"),
                ("role", "VARCHAR(40) DEFAULT 'user'"),
                ("password_hash", "TEXT"),
            ]

            for col_name, col_type in migrations:
                if col_name not in existing:
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  ✓ Added column: users.{col_name}")
                else:
                    print(f"  · Column already exists: users.{col_name}")

            # 3. Make phone nullable (it was NOT NULL before Google-only users)
            # This is safe to run even if already nullable
            conn.execute(text(
                "ALTER TABLE users ALTER COLUMN phone DROP NOT NULL"
            ))
            conn.commit()
            print("  ✓ users.phone is now nullable")
            conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
            conn.commit()
            print("  ✓ users.role backfilled to 'user'")

            # 4. Add missing columns to 'order_items' table
            order_item_cols = get_existing_columns(conn, "order_items")
            order_item_migrations = [
                ("dosage_instruction", "VARCHAR(120)"),
                ("strips_count", "INTEGER DEFAULT 1"),
                ("rx_required", "BOOLEAN DEFAULT FALSE"),
                ("prescription_file", "VARCHAR(300)"),
            ]
            for col_name, col_type in order_item_migrations:
                if col_name not in order_item_cols:
                    conn.execute(text(f"ALTER TABLE order_items ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"  ✓ Added column: order_items.{col_name}")
                else:
                    print(f"  · Column already exists: order_items.{col_name}")

            # 4b. Add missing columns to 'orders' table for audit trail
            order_cols = get_existing_columns(conn, "orders")
            order_migrations = [
                ("pharmacy_approved_by_name", "VARCHAR(120)"),
                ("pharmacy_approved_at", "TIMESTAMP WITH TIME ZONE"),
                ("last_status_updated_by_role", "VARCHAR(40)"),
                ("last_status_updated_by_name", "VARCHAR(120)"),
                ("last_status_updated_at", "TIMESTAMP WITH TIME ZONE"),
                ("delivery_address", "VARCHAR(255)"),
                ("delivery_lat", "DOUBLE PRECISION"),
                ("delivery_lng", "DOUBLE PRECISION"),
            ]
            for col_name, col_type in order_migrations:
                if col_name not in order_cols:
                    conn.execute(text(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"  ✓ Added column: orders.{col_name}")
                else:
                    print(f"  · Column already exists: orders.{col_name}")

            # 5. Add missing columns to 'medicines' table
            medicine_cols = get_existing_columns(conn, "medicines")
            if "image_url" not in medicine_cols:
                conn.execute(text("ALTER TABLE medicines ADD COLUMN image_url VARCHAR(500)"))
                conn.commit()
                print("  ✓ Added column: medicines.image_url")
            else:
                print("  · Column already exists: medicines.image_url")

            # 5b. Add location columns to 'pharmacy_stores' table
            ps_cols = get_existing_columns(conn, "pharmacy_stores")
            if "location_lat" not in ps_cols:
                conn.execute(text("ALTER TABLE pharmacy_stores ADD COLUMN location_lat DOUBLE PRECISION"))
                conn.commit()
                print("  ✓ Added column: pharmacy_stores.location_lat")
            else:
                print("  · Column already exists: pharmacy_stores.location_lat")
            if "location_lng" not in ps_cols:
                conn.execute(text("ALTER TABLE pharmacy_stores ADD COLUMN location_lng DOUBLE PRECISION"))
                conn.commit()
                print("  ✓ Added column: pharmacy_stores.location_lng")
            else:
                print("  · Column already exists: pharmacy_stores.location_lng")

            # 6. Add missing columns to 'notifications' table
            notif_cols = get_existing_columns(conn, "notifications")
            if "metadata_json" not in notif_cols:
                conn.execute(text("ALTER TABLE notifications ADD COLUMN metadata_json TEXT"))
                conn.commit()
                print("  ✓ Added column: notifications.metadata_json")
            else:
                print("  · Column already exists: notifications.metadata_json")
        finally:
            if lock_acquired:
                try:
                    conn.execute(text("SELECT pg_advisory_unlock(987654321)"))
                except Exception:
                    pass

    print("  ✓ Migration complete")
    _ensure_default_web_accounts()
    _ensure_default_pharmacy_stores()
    _ensure_sample_inventory_data()


def _ensure_default_web_accounts():
    defaults = [
        ("admin@rxcompute.com", "Arjun Verma", "admin", "admin123"),
        ("pharmacy@rxcompute.com", "Dr. Priya Patel", "pharmacy_store", "pharma123"),
        ("warehouse@rxcompute.com", "Rahul Menon", "warehouse", "warehouse123"),
    ]
    db = SessionLocal()
    try:
        for email, name, role, password in defaults:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                db.add(
                    User(
                        email=email,
                        name=name,
                        role=role,
                        password_hash=hash_password(password),
                        is_verified=True,
                        is_registered=True,
                    )
                )
            else:
                changed = False
                if not user.role or user.role == "user":
                    user.role = role
                    changed = True
                if not user.password_hash:
                    user.password_hash = hash_password(password)
                    changed = True
                if changed:
                    db.add(user)
        db.commit()
        print("  ✓ Default web role accounts verified")
    finally:
        db.close()


def _ensure_default_pharmacy_stores():
    defaults = [
        ("PH-001", "Central Pharmacy", "Mumbai Central", True, 35, 48),
        ("PH-002", "East Pharmacy", "Andheri East", True, 62, 44),
        ("PH-003", "South Pharmacy", "Colaba", False, 0, 41),
    ]
    db = SessionLocal()
    try:
        for node_id, name, location, active, load, stock_count in defaults:
            row = db.query(PharmacyStore).filter(PharmacyStore.node_id == node_id).first()
            if not row:
                db.add(
                    PharmacyStore(
                        node_id=node_id,
                        name=name,
                        location=location,
                        active=active,
                        load=load,
                        stock_count=stock_count,
                    )
                )
        db.commit()
        print("  ✓ Default pharmacy stores verified")
    finally:
        db.close()


def _ensure_sample_inventory_data():
    sample_medicines = [
        ("Paracetamol 650mg", "RXC000001", 39.0, "15 tablets", False, "Fever and pain relief"),
        ("Amoxicillin 500mg", "RXC000002", 129.0, "10 capsules", True, "Antibiotic (Rx required)"),
        ("Cetirizine 10mg", "RXC000003", 29.0, "10 tablets", False, "Allergy relief"),
        ("Atorvastatin 20mg", "RXC000004", 199.0, "10 tablets", True, "Cholesterol control (Rx required)"),
        ("Pantoprazole 40mg", "RXC000005", 89.0, "15 tablets", False, "Acidity and reflux"),
    ]
    db = SessionLocal()
    try:
        stores = db.query(PharmacyStore).all()
        for name, pzn, price, package, rx_required, desc in sample_medicines:
            med = db.query(Medicine).filter(Medicine.pzn == pzn).first()
            if not med:
                med = Medicine(
                    name=name,
                    pzn=pzn,
                    price=price,
                    package=package,
                    stock=120,
                    rx_required=rx_required,
                    description=desc,
                )
                db.add(med)
                db.flush()
            else:
                med.name = name
                med.price = price
                med.package = package
                med.rx_required = rx_required
                med.description = desc
                med.stock = max(med.stock or 0, 120)

            w_stock = db.query(WarehouseStock).filter(WarehouseStock.medicine_id == med.id).first()
            if not w_stock:
                w_stock = WarehouseStock(medicine_id=med.id, quantity=max((med.stock or 0) + 80, 200))
                db.add(w_stock)
            else:
                w_stock.quantity = max(w_stock.quantity or 0, (med.stock or 0) + 80, 200)

            for st in stores:
                p_stock = (
                    db.query(PharmacyStock)
                    .filter(PharmacyStock.pharmacy_store_id == st.id, PharmacyStock.medicine_id == med.id)
                    .first()
                )
                if not p_stock:
                    db.add(PharmacyStock(pharmacy_store_id=st.id, medicine_id=med.id, quantity=med.stock or 0))
                else:
                    p_stock.quantity = max(p_stock.quantity or 0, med.stock or 0)
        db.commit()
        print("  ✓ Sample admin/warehouse/pharmacy inventory verified (including Rx medicines)")
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
