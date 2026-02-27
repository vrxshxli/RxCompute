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

# Firebase — set GOOGLE_APPLICATION_CREDENTIALS env var on Render
# pointing to the service account JSON, or use FIREBASE_CONFIG env var.
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

# SMTP config (Maileroo defaults; can be overridden via env vars)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.maileroo.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "14ef21.2474.dac6161459055e179893f2a71ee584a0@a.maileroo.net")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "bcc8845204a6c26da0f71357").replace(" ", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FALLBACK_TO_EMAIL = os.getenv("SMTP_FALLBACK_TO_EMAIL", SMTP_FROM_EMAIL)

# Secret for external scheduler endpoint (e.g., cron-job.org)
JOB_RUN_KEY = os.getenv("JOB_RUN_KEY", "")

# Outgoing webhooks
WEBHOOK_TARGET_URL = os.getenv("WEBHOOK_TARGET_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WEBHOOK_TIMEOUT_SECONDS = int(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "8"))