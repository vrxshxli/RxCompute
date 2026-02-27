"""
Langfuse Configuration for RxCompute Agents.

SETUP (one-time):
  1. Go to https://cloud.langfuse.com → Sign up free
  2. Create project named "RxCompute"
  3. Settings → API Keys → copy public_key + secret_key
  4. Settings → Project → toggle ON "Public Access"
  5. Copy the public URL — this is what judges open during demo
  6. Add to your Backend/.env file:

     LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
     LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx
     LANGFUSE_HOST=https://cloud.langfuse.com

If keys are not set, everything still works — Langfuse tracing
is just silently disabled. No crashes, no errors.
"""

import os
from dotenv import load_dotenv

load_dotenv()

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_ENABLED = bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)

# Initialize Langfuse client (used for manual trace creation)
_langfuse_client = None

def get_langfuse():
    """Get Langfuse client. Returns None if not configured."""
    global _langfuse_client
    if not LANGFUSE_ENABLED:
        return None
    if _langfuse_client is None:
        from langfuse import Langfuse
        _langfuse_client = Langfuse(
            public_key=LANGFUSE_PUBLIC_KEY,
            secret_key=LANGFUSE_SECRET_KEY,
            host=LANGFUSE_HOST,
        )
    return _langfuse_client


def configure_langfuse_decorators():
    """
    Configure the @observe decorator to use our Langfuse keys.
    Call this ONCE at app startup (in main.py).
    """
    if not LANGFUSE_ENABLED:
        print("⚠ Langfuse not configured — agent tracing disabled")
        return

    os.environ["LANGFUSE_PUBLIC_KEY"] = LANGFUSE_PUBLIC_KEY
    os.environ["LANGFUSE_SECRET_KEY"] = LANGFUSE_SECRET_KEY
    os.environ["LANGFUSE_HOST"] = LANGFUSE_HOST
    print(f"✓ Langfuse configured — traces at {LANGFUSE_HOST}")