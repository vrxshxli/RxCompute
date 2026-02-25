import hashlib
import hmac
import json
from urllib import error, request

from sqlalchemy.orm import Session

from config import WEBHOOK_TARGET_URL, WEBHOOK_SECRET, WEBHOOK_TIMEOUT_SECONDS
from models.webhook_log import WebhookLog


def dispatch_webhook(db: Session, event_type: str, payload: dict) -> WebhookLog | None:
    if not WEBHOOK_TARGET_URL:
        return None

    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    headers = {"Content-Type": "application/json", "X-Rx-Event": event_type}
    if WEBHOOK_SECRET:
        signature = hmac.new(
            WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        headers["X-Rx-Signature"] = f"sha256={signature}"

    req = request.Request(WEBHOOK_TARGET_URL, data=body, headers=headers, method="POST")
    status_code = None
    response_body = None
    error_message = None
    try:
        with request.urlopen(req, timeout=WEBHOOK_TIMEOUT_SECONDS) as resp:
            status_code = resp.status
            response_body = resp.read().decode("utf-8", errors="ignore")[:2000]
    except error.HTTPError as exc:
        status_code = exc.code
        response_body = exc.read().decode("utf-8", errors="ignore")[:2000]
        error_message = f"HTTPError: {exc}"
    except Exception as exc:
        error_message = f"RequestError: {exc}"

    log = WebhookLog(
        event_type=event_type,
        target_url=WEBHOOK_TARGET_URL,
        payload=json.dumps(payload, ensure_ascii=True),
        response_status=status_code,
        response_body=response_body,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
