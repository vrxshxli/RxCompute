import psycopg2
import psycopg2.extras
from .config import DATABASE_URL

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True

def upsert_user(uid, email, phone, name, photo_url, provider, role: str | None = None):
    q = (
        """
        INSERT INTO users (uid, email, phone, name, photo_url, provider, role)
        VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, 'user'))
        ON CONFLICT (uid) DO UPDATE SET
          email = EXCLUDED.email,
          phone = EXCLUDED.phone,
          name = EXCLUDED.name,
          photo_url = EXCLUDED.photo_url,
          provider = EXCLUDED.provider,
          role = EXCLUDED.role
        RETURNING id, uid, email, phone, name, photo_url, provider, role, created_at, updated_at;
        """
    )
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(q, (uid, email, phone, name, photo_url, provider, role))
        return cur.fetchone()


def get_user_by_uid(uid: str):
    q = "SELECT id, uid, email, phone, name, photo_url, provider, role, created_at, updated_at FROM users WHERE uid = %s;"
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(q, (uid,))
        return cur.fetchone()


def update_user_role(uid: str, role: str):
    q = (
        "UPDATE users SET role = %s WHERE uid = %s RETURNING id, uid, email, phone, name, photo_url, provider, role, created_at, updated_at;"
    )
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(q, (role, uid))
        return cur.fetchone()
