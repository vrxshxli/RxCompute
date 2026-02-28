# RxCompute Project And API Guide

This document gives a practical overview of the project architecture, core flows, and backend endpoints.

## 1) Project Structure

- `Backend/` - FastAPI + SQLAlchemy backend, safety agents, notification delivery, migrations.
- `RxCompute-Web-main/` - React web app for admin, pharmacy, warehouse dashboards.
- `Application/` - Flutter mobile app for users (chat, orders, notifications, profile, voice).

## 2) Core Backend Architecture

- `main.py`
  - Initializes Firebase Admin.
  - Runs startup migrations (`migrate.py`).
  - Includes all routers.
  - Mounts `/uploads` static directory.
- `database.py`
  - SQLAlchemy engine/session/base setup.
- `models/`
  - Domain models (`User`, `Medicine`, `Order`, `Notification`, `WarehouseStock`, etc.).
- `schemas/`
  - Pydantic request/response schemas.
- `routers/`
  - Feature-specific APIs (auth, orders, notifications, warehouse, safety, chat, etc.).
- `services/`
  - Notification delivery (push/email), refill reminders, webhooks.
- `saftery_policies_agents/`
  - LangGraph safety orchestration and deterministic safety rule engine.

## 3) Key Domain Flows

### 3.1 Order Flow

1. User places order (`POST /orders/`).
2. Safety agent runs before placement.
3. If blocked -> order rejected with reasons.
4. If allowed -> order is created, notifications sent.
5. Pharmacy verifies (`PUT /orders/{id}/status`) with safety re-check.
6. Admin handles logistics statuses.

### 3.2 Safety Flow

- Implemented via LangGraph (`process_with_safety`).
- Runs in:
  - order create,
  - pharmacy manual verify,
  - pharmacy auto-review.
- Current checks include:
  - prescription requirement,
  - medicine existence,
  - stock checks,
  - dosage/strips/day consistency,
  - OCR text extraction (Tesseract) and evidence matching,
  - interaction checks.

### 3.3 Notification Flow

- In-app notifications stored in `notifications` table.
- Push via Firebase.
- Email via SMTP/Maileroo fallback.
- Delivery health debug endpoint available for admin.

### 3.4 Inventory Flow

- Separate stock tables for admin medicine stock, warehouse stock, and pharmacy stock.
- Transfer directions supported:
  - admin -> warehouse,
  - warehouse -> admin,
  - warehouse -> pharmacy,
  - pharmacy -> warehouse request.

## 4) Backend API Endpoints

Below are route groups and primary endpoints.

## Health

- `GET /` - API health check.

## Auth (`/auth`)

- `POST /auth/google`
- `POST /auth/send-otp`
- `POST /auth/verify-otp`
- `POST /auth/web-login`

## Users (`/users`)

- `POST /users/register`
- `GET /users/me`
- `PUT /users/me`
- `GET /users/`

## Medicines (`/medicines`)

- `GET /medicines/`
- `GET /medicines/{medicine_id}`
- `POST /medicines/`
- `PUT /medicines/{medicine_id}`
- `DELETE /medicines/{medicine_id}`
- `PUT /medicines/{medicine_id}/add-stock`
- `POST /medicines/import-csv`

## Orders (`/orders`)

- `GET /orders/`
- `GET /orders/{order_id}`
- `POST /orders/`
- `PUT /orders/{order_id}/status`

## Notifications (`/notifications`)

- `GET /notifications/`
- `PUT /notifications/{notification_id}/read`
- `PUT /notifications/read-all`
- `GET /notifications/delivery-health`
- `GET /notifications/safety-events`
- `POST /notifications/test-delivery`
- `GET /notifications/test-delivery`

## Safety (`/safety`)

- `POST /safety/check`
- `POST /safety/check-single/{medicine_id}`

## Chat (`/chat`)

- `POST /chat/upload-prescription`

## User Medications (`/user-medications`)

- `GET /user-medications/`
- `POST /user-medications/`
- `PUT /user-medications/{medication_id}`
- `DELETE /user-medications/{medication_id}`

## Home (`/home`)

- `GET /home/summary`

## Pharmacy Stores (`/pharmacy-stores`)

- `GET /pharmacy-stores/`
- `POST /pharmacy-stores/`
- `PUT /pharmacy-stores/{store_id}`

## Warehouse (`/warehouse`)

- `GET /warehouse/stock`
- `GET /warehouse/pharmacy-stock`
- `GET /warehouse/stock-breakdown`
- `GET /warehouse/pharmacy-options`
- `GET /warehouse/medicines/csv-template`
- `POST /warehouse/medicines`
- `POST /warehouse/medicines/bulk`
- `PUT /warehouse/medicines/{medicine_id}`
- `DELETE /warehouse/medicines/{medicine_id}`
- `POST /warehouse/medicines/import-csv`
- `GET /warehouse/transfers`
- `POST /warehouse/transfers/admin-to-warehouse`
- `POST /warehouse/transfers/warehouse-to-admin`
- `POST /warehouse/transfers/warehouse-to-pharmacy`
- `POST /warehouse/transfers/pharmacy-request`
- `PUT /warehouse/transfers/{transfer_id}/status`

## Scheduler (`/scheduler`)

- `POST /scheduler/route`
- `GET /scheduler/grid-status`
- `POST /scheduler/simulate`

## Jobs (`/jobs`)

- `GET /jobs/run-refill-reminders`

## Webhooks (`/webhooks`)

- `GET /webhooks/logs`
- `POST /webhooks/test`

## 5) Safety Agent Notes (Current)

- LangGraph is the orchestrator.
- Rx verification is evidence-based:
  - Tesseract OCR extracts text from uploaded image.
  - Medicine name tokens must appear in OCR text.
  - Dosage instruction must be explicit and match.
  - Treatment duration must be present and parseable.
  - Ordered strips must satisfy computed required strips based on duration + daily dosage.
- If any required evidence is missing -> status `blocked`.

## 6) Deployment Notes

- Ensure backend runtime includes `tesseract-ocr` binary.
- Python dependencies include:
  - `pytesseract`
  - `Pillow`
- If Tesseract is missing, prescription verification will fail safely (blocked).

## 7) Mobile Notification Notes

- Foreground: in-app + local notification banner + voice summary.
- Background/closed: OS push shown; voice resumes on app foreground/resume.

## 8) Recommended Operational Checks

- `GET /notifications/delivery-health` for notification and SMTP visibility.
- `GET /notifications/safety-events` for safety trace-level activity.
- Verify pharmacy orders with Rx use cases:
  - wrong image -> reject,
  - missing dosage/day -> reject,
  - insufficient strips for days -> reject,
  - matching evidence -> allow verify.

## 9) Database Tables (Detailed)

This section maps each SQLAlchemy model to table purpose, important columns, and relationships.

### `users`

- Purpose: stores all account types (`user`, `admin`, `pharmacy_store`, `warehouse`).
- Key columns:
  - `id` (PK)
  - `phone` (unique, nullable)
  - `google_id` (unique, nullable)
  - `name`, `age`, `gender`, `email`
  - `location_text`, `location_lat`, `location_lng`
  - `role`
  - `password_hash`
  - `push_token`
  - `allergies`, `conditions`
  - `is_verified`, `is_registered`
  - `created_at`, `updated_at`

### `otps`

- Purpose: OTP verification records.
- Key columns:
  - `id` (PK)
  - `phone`
  - `otp`
  - `created_at`

### `medicines`

- Purpose: master medicine catalog + admin stock baseline.
- Key columns:
  - `id` (PK)
  - `name`
  - `pzn` (unique)
  - `price`
  - `package`
  - `stock`
  - `rx_required`
  - `description`
  - `image_url`
  - `created_at`, `updated_at`

### `orders`

- Purpose: customer order header.
- Key columns:
  - `id` (PK)
  - `order_uid` (unique business id, indexed)
  - `user_id` (FK -> `users.id`)
  - `status` (`pending/verified/...`)
  - `total`
  - `pharmacy` (assigned node id, ex `PH-U001`)
  - `payment_method`
  - `delivery_address`, `delivery_lat`, `delivery_lng`
  - status audit fields:
    - `pharmacy_approved_by_name`, `pharmacy_approved_at`
    - `last_status_updated_by_role`, `last_status_updated_by_name`, `last_status_updated_at`
  - `created_at`, `updated_at`

### `order_items`

- Purpose: line items for each order.
- Key columns:
  - `id` (PK)
  - `order_id` (FK -> `orders.id`)
  - `medicine_id` (FK -> `medicines.id`)
  - `name`, `quantity`, `price`
  - `dosage_instruction`
  - `strips_count`
  - `rx_required` (captured snapshot at order-time)
  - `prescription_file` (Cloudinary URL or local uploads path)

### `notifications`

- Purpose: in-app notification inbox.
- Key columns:
  - `id` (PK)
  - `user_id` (FK -> `users.id`)
  - `type` (`refill/order/safety/system`)
  - `title`, `body`
  - `metadata_json` (trace payloads including OCR/safety details)
  - `is_read`, `has_action`
  - `created_at`

### `user_medications`

- Purpose: tracked personal medicines for refill reminders.
- Key columns:
  - `id` (PK)
  - `user_id` (FK -> `users.id`)
  - `medicine_id` (FK -> `medicines.id`, nullable for custom entries)
  - `custom_name`
  - `dosage_instruction`
  - `frequency_per_day`
  - `quantity_units`
  - `created_at`, `updated_at`

### `pharmacy_stores`

- Purpose: pharmacy nodes and capacity metadata.
- Key columns:
  - `id` (PK)
  - `node_id` (unique, indexed)
  - `name`, `location`
  - `location_lat`, `location_lng`
  - `active`
  - `load`
  - `stock_count`
  - `created_at`, `updated_at`

### `warehouse_stock`

- Purpose: warehouse inventory per medicine.
- Key columns:
  - `id` (PK)
  - `medicine_id` (FK -> `medicines.id`, unique)
  - `quantity`
  - `updated_at`

### `warehouse_transfers`

- Purpose: transfer ledger between admin/warehouse/pharmacy.
- Key columns:
  - `id` (PK)
  - `medicine_id` (FK -> `medicines.id`)
  - `quantity`
  - `direction` (`admin_to_warehouse`, `warehouse_to_pharmacy`, etc.)
  - `status` (`requested`, `picking`, `packed`, `dispatched`, `received`)
  - `pharmacy_store_id` (FK -> `pharmacy_stores.id`, nullable)
  - `note`
  - `created_by_user_id` (FK -> `users.id`)
  - `created_at`, `updated_at`

### `pharmacy_stock`

- Purpose: per-store pharmacy inventory.
- Key columns:
  - `id` (PK)
  - `pharmacy_store_id` (FK -> `pharmacy_stores.id`)
  - `medicine_id` (FK -> `medicines.id`)
  - `quantity`
  - `updated_at`
- Constraint:
  - unique pair (`pharmacy_store_id`, `medicine_id`)

### `webhook_logs`

- Purpose: outgoing webhook observability/audit.
- Key columns:
  - `id` (PK)
  - `event_type`
  - `target_url`
  - `payload`
  - `response_status`, `response_body`, `error_message`
  - `created_at`

## 10) Relationship Map (Quick)

- `users (1) -> (many) orders`
- `orders (1) -> (many) order_items`
- `medicines (1) -> (many) order_items`
- `users (1) -> (many) notifications`
- `users (1) -> (many) user_medications`
- `medicines (1) -> (1) warehouse_stock` (by unique medicine id)
- `pharmacy_stores (1) -> (many) pharmacy_stock`
- `medicines (1) -> (many) pharmacy_stock`
- `pharmacy_stores (1) -> (many) warehouse_transfers`
- `medicines (1) -> (many) warehouse_transfers`

## 11) Code Walkthrough (Critical Files)

### Backend

- `Backend/main.py`
  - App bootstrap, Firebase init, startup migration, router registration.
- `Backend/migrate.py`
  - Idempotent schema upgrades, defaults, and sample data seeding.
- `Backend/routers/orders.py`
  - Order creation, pharmacy/admin status transitions, stock reservation, nearby pharmacy assignment, safety hooks.
- `Backend/routers/warehouse.py`
  - Warehouse stock CRUD, transfer workflows, pharmacy request flows.
- `Backend/routers/notifications.py`
  - Notification APIs, delivery health, safety events listing.
- `Backend/saftery_policies_agents/graph.py`
  - LangGraph entry (`process_with_safety`) and state pipeline.
- `Backend/saftery_policies_agents/safety_agent.py`
  - Deterministic policy rules, OCR extraction, medicine/dosage/strips/day checks.
- `Backend/services/notifications.py`
  - In-app notification creation, push delivery, SMTP + API email fallback.

### Web

- `RxCompute-Web-main/src/App.js`
  - Role-based navigation/routing and shared providers.
- `RxCompute-Web-main/src/context/NotificationContext.js`
  - Polling, dedupe, sound, spoken safety alerts.
- `RxCompute-Web-main/src/pages/pharmacy/OrderVerify.js`
  - Live safety check UI and verify/reject controls.
- `RxCompute-Web-main/src/pages/admin/AgentTraces.js`
  - Safety trace rendering from `notifications/safety-events`.

### Mobile

- `Application/lib/main.dart`
  - Firebase setup, app bootstrap, providers.
- `Application/lib/features/home/screens/main_shell.dart`
  - FCM listeners, voice assistant, spoken alert behavior, notification sync.
- `Application/lib/features/chat/bloc/chat_bloc.dart`
  - Conversational order flow, prescription upload integration, safety-aware ordering.
- `Application/lib/data/repositories/*`
  - API interaction layer used by BLoCs/screens.
