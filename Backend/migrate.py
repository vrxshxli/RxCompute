"""
Simple migration script — adds missing columns to existing tables.
Safe to run multiple times (checks before altering).
"""

from sqlalchemy import text, inspect
from database import engine, Base

# Import all models so Base.metadata knows about them
from models.user import User, OTP  # noqa: F401
from models.medicine import Medicine  # noqa: F401
from models.order import Order, OrderItem  # noqa: F401
from models.notification import Notification  # noqa: F401
from models.user_medication import UserMedication  # noqa: F401


def get_existing_columns(conn, table_name: str) -> set:
    """Get the set of column names that already exist in a table."""
    insp = inspect(conn)
    if not insp.has_table(table_name):
        return set()
    return {col["name"] for col in insp.get_columns(table_name)}


def migrate():
    with engine.connect() as conn:
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

        # 5. Add missing columns to 'medicines' table
        medicine_cols = get_existing_columns(conn, "medicines")
        if "image_url" not in medicine_cols:
            conn.execute(text("ALTER TABLE medicines ADD COLUMN image_url VARCHAR(500)"))
            conn.commit()
            print("  ✓ Added column: medicines.image_url")
        else:
            print("  · Column already exists: medicines.image_url")

    print("  ✓ Migration complete")


if __name__ == "__main__":
    migrate()
