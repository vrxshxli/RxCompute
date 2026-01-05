import os
import sys

# Ensure server-py is on the Python path so package-relative imports work
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_PY = os.path.join(BASE_DIR, 'server-py')
if SERVER_PY not in sys.path:
    sys.path.insert(0, SERVER_PY)

# Import the FastAPI app from server-py/app/main.py
from app.main import app  # noqa: E402
