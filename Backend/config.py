import os

# Render provides DATABASE_URL starting with "postgres://..."
# SQLAlchemy 2.x requires "postgresql://..." — patch it here.
_raw_db_url = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Deepak2003@localhost:5432/rx_db",
)
DATABASE_URL = _raw_db_url.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.getenv("SECRET_KEY", "rx-compute-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
