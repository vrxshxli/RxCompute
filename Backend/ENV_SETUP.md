# Backend Environment Setup

Use these keys in your local environment and Render environment.

## Required

- `DATABASE_URL`
- `SECRET_KEY`
- `FIREBASE_SERVICE_ACCOUNT`

## Email (Custom SMTP / Gmail)

- `SMTP_HOST` = `smtp.gmail.com` (or your provider host)
- `SMTP_PORT` = `587` (TLS) or `465` (SSL)
- `SMTP_USER` = `deepakm7778@gmail.com`
- `SMTP_PASSWORD` = your-gmail-app-password (spaces are automatically stripped)
- `SMTP_FROM_EMAIL` = `deepakm7778@gmail.com`
- `SMTP_FALLBACK_TO_EMAIL` = `deepakm7778@gmail.com` (used if user profile email is empty)

## Optional

- `FIREBASE_PROJECT_ID`
- `JOB_RUN_KEY` (required only if using external free scheduler without Render cron)
- `WEBHOOK_TARGET_URL` (where order webhooks should be sent)
- `WEBHOOK_SECRET` (optional signature secret, sent as `X-Rx-Signature`)
- `WEBHOOK_TIMEOUT_SECONDS` (default `8`)

## Role-Based Web Login

- Backend now supports roles in `users.role`:
  - `user`
  - `admin`
  - `pharmacy_store`
  - `warehouse`
- Web login endpoint:
  - `POST /auth/web-login`
- Default seeded staff credentials (created by migration if missing):
  - `admin@rxcompute.com` / `admin123`
  - `pharmacy@rxcompute.com` / `pharma123`
  - `warehouse@rxcompute.com` / `warehouse123`
- Web app routes:
  - `/login/admin`
  - `/login/pharmacy`
  - `/login/warehouse`

## Daily Refill Reminder (Render Cron)

- Cron job runs daily (configured in `render.yaml`) and triggers refill reminders
  for medicines with `days_left <= 4`.
- Current schedule is set for **09:00 AM IST daily** (`30 3 * * *` in UTC cron).
- Make sure cron service has:
  - `DATABASE_URL`
  - `FIREBASE_SERVICE_ACCOUNT`

## Daily Refill Reminder (No Card / External Scheduler)

- If you cannot use Render Cron (card required), use free `cron-job.org`.
- Set `JOB_RUN_KEY` in Render web service env (random long secret).
- Configure cron-job.org to call daily:
  - `GET https://rxcompute-api.onrender.com/jobs/run-refill-reminders?key=YOUR_JOB_RUN_KEY`
- Suggested schedule for 09:00 IST:
  - `03:30 UTC` daily in cron-job.org

## Debug Endpoint

- `POST /notifications/test-delivery`
  - creates one in-app test notification
  - tries push delivery to `push_token`
  - tries email delivery to profile email (or fallback email)
- `GET /notifications/test-delivery` (browser-friendly alias)

## Webhook Endpoints

- Outgoing order webhooks are sent on:
  - order creation
  - order status update
- Admin/staff APIs:
  - `GET /webhooks/logs`
  - `POST /webhooks/test`

## FIREBASE_SERVICE_ACCOUNT Format

Set full Firebase service-account JSON in one line:

```text
{"type":"service_account","project_id":"your-project-id","private_key":"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n","client_email":"firebase-adminsdk-xxx@your-project-id.iam.gserviceaccount.com", ...}
```

`\\n` handling for private key is already supported by backend startup code.
