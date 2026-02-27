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
SMTP_PORT = int(os.getenv("SMTP_PORT", "2525"))
DEFAULT_MAILEROO_SMTP_USER = "rxcompute@35ddfa3956a414ee.maileroo.org"
DEFAULT_MAILEROO_SMTP_PASSWORD = "f71f20a46ffb0046b73d746b"
DEFAULT_MAILEROO_API_KEY = "5bb8ad0fa0487a4f2bb77d40d90c7565974f89d1054160c752eed794232b4d6a"
SMTP_USER = os.getenv("SMTP_USER", DEFAULT_MAILEROO_SMTP_USER)
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", DEFAULT_MAILEROO_SMTP_PASSWORD).replace(" ", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FALLBACK_TO_EMAIL = os.getenv("SMTP_FALLBACK_TO_EMAIL", SMTP_FROM_EMAIL)
MAILEROO_API_KEY = os.getenv("MAILEROO_API_KEY", DEFAULT_MAILEROO_API_KEY)
MAILEROO_API_URL = os.getenv("MAILEROO_API_URL", "https://smtp.maileroo.com/api/v2/emails")

# Prevent stale Gmail env from breaking delivery on restricted networks.
if "gmail.com" in SMTP_HOST.lower() and os.getenv("ALLOW_GMAIL_SMTP", "").lower() not in {"1", "true", "yes"}:
    SMTP_HOST = "smtp.maileroo.com"

# Guard against stale Render vars pointing to Gmail sender/account.
if SMTP_USER.lower().endswith("@gmail.com"):
    SMTP_USER = DEFAULT_MAILEROO_SMTP_USER
    SMTP_PASSWORD = DEFAULT_MAILEROO_SMTP_PASSWORD
if SMTP_FROM_EMAIL.lower().endswith("@gmail.com"):
    SMTP_FROM_EMAIL = SMTP_USER

# Maileroo API keys are domain-restricted; ensure sender domain stays authorized.
_smtp_user_domain = SMTP_USER.split("@")[-1].lower() if "@" in SMTP_USER else ""
_smtp_from_domain = SMTP_FROM_EMAIL.split("@")[-1].lower() if "@" in SMTP_FROM_EMAIL else ""
if _smtp_user_domain and _smtp_from_domain and _smtp_from_domain != _smtp_user_domain:
    if os.getenv("ALLOW_CUSTOM_FROM_DOMAIN", "").lower() not in {"1", "true", "yes"}:
        SMTP_FROM_EMAIL = SMTP_USER

# Secret for external scheduler endpoint (e.g., cron-job.org)
JOB_RUN_KEY = os.getenv("JOB_RUN_KEY", "")

# Outgoing webhooks
WEBHOOK_TARGET_URL = os.getenv("WEBHOOK_TARGET_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
WEBHOOK_TIMEOUT_SECONDS = int(os.getenv("WEBHOOK_TIMEOUT_SECONDS", "8"))

# Cloudinary (prescription image storage)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_UPLOAD_PRESET = os.getenv("CLOUDINARY_UPLOAD_PRESET", "")
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "rxcompute/prescriptions")

# Gemini (safety OCR validation)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBbaJoIV5H2IvsMybbgA8FeysrCqHFvmVc")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro-latest")