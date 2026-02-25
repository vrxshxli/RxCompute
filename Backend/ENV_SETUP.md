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
- `SMTP_PASSWORD` = nyur amcv pgmu dvau
- `SMTP_FROM_EMAIL` = `deepakm7778@gmail.com`

## Optional

- `FIREBASE_PROJECT_ID`

## Daily Refill Reminder (Render Cron)

- Cron job runs daily (configured in `render.yaml`) and triggers refill reminders
  for medicines with `days_left <= 4`.
- Current schedule is set for **09:00 AM IST daily** (`30 3 * * *` in UTC cron).
- Make sure cron service has:
  - `DATABASE_URL`
  - `FIREBASE_SERVICE_ACCOUNT`

## FIREBASE_SERVICE_ACCOUNT Format

Set full Firebase service-account JSON in one line:

```text
{"type":"service_account","project_id":"your-project-id","private_key":"-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n","client_email":"firebase-adminsdk-xxx@your-project-id.iam.gserviceaccount.com", ...}
```

`\\n` handling for private key is already supported by backend startup code.
