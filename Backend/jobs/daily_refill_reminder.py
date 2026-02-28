import json
import os
import tempfile

import firebase_admin
from firebase_admin import credentials

from database import SessionLocal
from services.refill_reminders import trigger_daily_refill_notifications_for_all_users
from prediction_agent.prediction_agent import run_prediction_scan

def init_firebase():
    if firebase_admin._apps:
        return
    firebase_sa = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if not firebase_sa:
        return
    try:
        sa_dict = json.loads(firebase_sa)
    except json.JSONDecodeError:
        cleaned = firebase_sa.strip().strip("'").strip('"')
        try:
            sa_dict = json.loads(cleaned)
        except json.JSONDecodeError:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
            tmp.write(firebase_sa)
            tmp.close()
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
            firebase_admin.initialize_app()
            return

    if "private_key" in sa_dict and "\\n" in sa_dict["private_key"]:
        sa_dict["private_key"] = sa_dict["private_key"].replace("\\n", "\n")
    cred = credentials.Certificate(sa_dict)
    firebase_admin.initialize_app(cred)


def main():
    init_firebase()
    db = SessionLocal()
    try:
        # Existing refill reminders
        count = trigger_daily_refill_notifications_for_all_users(db)
        print(f"Refill reminders: {count}")

        # NEW: Full prediction scan with velocity + risk + demand
        result = run_prediction_scan()
        print(f"Prediction scan: {result['risk_summary']}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
