# RxCompute Agent Automation Workflow

This document explains how automation is implemented per agent in RxCompute, step by step, in workflow format.

## 1) System-Level Automation Workflow (End-to-End)

1. **User interaction starts a flow**
   - Input can come from Flutter chat (text/voice), refill action, admin action, or scheduled jobs.
   - Frontend calls backend APIs (`/chat/*`, `/orders/*`, `/predictions/*`, `/demand-forecast/*`).

2. **Backend router validates and builds context**
   - Auth + RBAC checks (`user`, `admin`, `pharmacy`, `pharmacy_store`, `warehouse`).
   - Agent context retrieval (medicine catalog, user medication history, order history).

3. **Agent orchestration executes**
   - LangGraph-style sequencing: safety, exception, scheduler, order execution, prediction/forecast as required.
   - Critical safety decisions are deterministic (rule-driven) for auditability.

4. **State is persisted + notifications are emitted**
   - Order status, cancellation reason, safety reason, exception status, forecast records are stored.
   - Notifications are pushed to relevant users/roles.

5. **Traces are generated for observability**
   - Agent step metadata and workflow events are published as traces.
   - Admin dashboard and workflow pages consume these traces.

6. **Frontend auto-refresh surfaces live operations**
   - Admin and pharmacy dashboards poll and refresh data.
   - Users see updated order status, cancellation reasons, and agent outcomes.

---

## 2) Safety Agent Workflow (Deterministic Guardrail)

### Purpose
Prevent unsafe or policy-violating medicine orders before fulfillment.

### Trigger
- Order creation flow
- Pharmacy verification flow
- Re-checks in automated status transitions

### Step-by-step workflow
1. **Normalize order + medicine identity**
   - Normalize medicine names/tokens to catch variant spellings.
   - Resolve `medicine_id` and normalized name keys for checks.

2. **Run duplicate and active-stock checks**
   - Verify whether the same user already has active supply/history/in-flight order for the same medicine.
   - If duplicate risk exists, create hard reject reason.

3. **Validate prescription requirement**
   - If medicine requires Rx, enforce prescription image and text checks.

4. **Run OCR + semantic medicine match**
   - Extract text from prescription image.
   - Match medicine name using strict + fuzzy methods (supports broken tokens/handwritten-like splits).
   - Validate dosage semantics (exact phrase, numeric schedule, mapped frequency words, meaningful token matches).

5. **Generate decision**
   - **Pass**: move forward in order workflow.
   - **Reject/Hold**: block progression, return clear user/pharmacy reason.

6. **Publish safety trace**
   - Attach metadata (decision reason, OCR confidence, token hits, duplicate hit source).
   - Send to admin trace feed.

### Output
- `allow`, `reject`, or `manual_review`
- Rich reason payload for user, pharmacy, and admin.

---

## 3) Exception Agent Workflow (Operational Recovery)

### Purpose
Handle non-happy-path conditions and route them for resolution.

### Trigger
- Safety rejects
- Verification mismatches
- Inventory/fulfillment anomalies
- Agent execution failures

### Step-by-step workflow
1. **Classify exception type**
   - Safety conflict, stock issue, verification mismatch, processing failure, etc.

2. **Create/queue exception item**
   - Add to exception queue with severity, owner role, and context metadata.

3. **Notify responsible role**
   - Pharmacy/admin/warehouse gets actionable alert.

4. **Track resolution lifecycle**
   - Pending -> in_progress -> resolved/rejected with notes.

5. **Publish trace and resolution event**
   - Resolution steps become visible in workflow timeline.

### Output
- Actionable exception queue entries + audit trail.

---

## 4) Scheduler Agent Workflow (Fulfillment Routing)

### Purpose
Auto-assign eligible pharmacy/store and advance fulfillment stages.

### Trigger
- Safety-approved order
- Retry/reassignment events

### Step-by-step workflow
1. **Collect candidate pharmacies**
   - Filter by role eligibility, availability, and operational constraints.

2. **Score/select best candidate**
   - Choose route target based on scheduling policy.

3. **Assign and update order**
   - Persist assignment and move state to verification/picking pipeline.

4. **Emit transition traces**
   - Log automation step (assigned, verified, picking, packed, dispatched, delivered).

5. **Notify participants**
   - Pharmacy and user receive status updates.

### Output
- Auto-routed order with staged status transitions.

---

## 5) Order Agent Workflow (Conversation -> Confirmed Order)

### Purpose
Convert conversational intent into valid, traceable medicine orders.

### Trigger
- Chat command to place order
- Refill confirmation action

### Step-by-step workflow
1. **Extract intent and entities**
   - Medicine, quantity, dosage intent, cancellation/new-chat/change-medicine commands.

2. **Validate order payload**
   - User auth, medicine validity, quantity and constraints.

3. **Call safety gate**
   - Mandatory safety pass required before placement.

4. **Apply strict duplicate hard gate**
   - Independent duplicate blocker at order stage to prevent bypass.

5. **Create order record**
   - Persist order + initial status + reason fields where applicable.

6. **Kick off post-create automation**
   - Scheduler route + notifications + trace publication.

### Output
- Placed/cancelled/blocked order with reasoned state.

---

## 6) Prediction Agent Workflow (Refill Intelligence)

### Purpose
Predict likely refill needs and trigger proactive journeys.

### Trigger
- Scheduled analysis
- Admin/pharmacy/manual trigger

### Step-by-step workflow
1. **Read historical medication/order data**
   - Evaluate dose cadence, prior purchases, and recency.

2. **Compute refill candidates**
   - Identify users likely nearing stock depletion.

3. **Create recommendations/alerts**
   - Send user-facing refill prompts and operations signals.

4. **User confirms refill (optional path)**
   - Confirmation re-enters order workflow through safety + scheduler.

5. **Trace prediction actions**
   - Prediction generation and conversions are logged.

### Output
- Ranked refill opportunities and downstream conversion signals.

---

## 7) Demand Forecast Agent Workflow (Inventory Risk Automation)

### Purpose
Forecast medicine demand and generate reorder-risk alerts.

### Trigger
- Scheduled forecast run
- Manual run from admin traces page

### Step-by-step workflow
1. **Ingest historical demand signals**
   - Orders, recent trends, medicine-level movement.

2. **Generate forecast horizon**
   - Predict expected demand for configurable days window.

3. **Compute risk and reorder recommendation**
   - Mark levels like critical/high/medium based on projected gaps.

4. **Persist forecast output**
   - Store alert details for analytics and reporting.

5. **Notify stakeholder roles**
   - Admin and pharmacy receive forecast alerts.

6. **Publish forecast traces**
   - Agent execution appears in admin traces and workflow timeline.

### Output
- Demand alerts, risk-ranked medicines, and forecast execution traces.

---

## 8) Conversational AI Workflow (Flutter Chat + Voice)

### Purpose
Provide robust natural interaction for ordering and order controls.

### Trigger
- User text message
- User voice input (STT)

### Step-by-step workflow
1. **Capture input**
   - Text or voice command from chat UI.

2. **Intent interpretation**
   - Parse intents (order, cancel order, new chat, change medicine, end chat).

3. **Command-safe state update**
   - For `new chat` and `change medicine`, reset draft/selection state safely.
   - For `cancel order`, call cancel endpoint for eligible order.

4. **Order-building loop**
   - Ask follow-up prompts until required entities are complete.

5. **Handoff to order workflow**
   - Final intent triggers order agent path.

6. **Voice orchestration guard**
   - Stop TTS before STT start to avoid audio feedback conflict.

### Output
- Natural-language driven ordering with explicit control commands.

---

## 9) Observability and Trace Workflow

### Purpose
Make every automated decision explainable in admin/pharmacy operations.

### Step-by-step workflow
1. **Capture per-step metadata**
   - Agent name, order/task id, status transition, reason, confidence/context fields.

2. **Store notification + trace records**
   - Backend writes trace-like records through notification/tracing channels.

3. **Expose trace APIs**
   - Dashboards fetch agent traces with pagination and filters.

4. **Render as workflow timeline**
   - Admin sees order/task-wise sequence of execution steps.

5. **Auto-refresh for live operations**
   - Polling keeps pages near-real-time without manual refresh.

### Output
- Auditable, searchable history of automation.

---

## 10) Frontend Automation Surfaces (Where each workflow appears)

- **Flutter user app**
  - Chat-driven ordering, cancellation, change medicine, new chat.
  - Order history/tracking shows cancellation reasons.

- **Admin web**
  - Dashboard live activity and agent traces.
  - Agent workflow timeline for step-by-step execution visibility.
  - Manual trigger for demand forecast run.

- **Pharmacy web**
  - Order verification with safety-consistent gating.
  - Exceptions queue with explicit error visibility.
  - Analytics with demand alert cards and top-risk items.

---

## 11) Design Principles Used in Automation

1. **Deterministic safety for critical decisions**
   - Hard rules over free-form LLM decisions for rejection/approval gates.

2. **LLM where flexibility is needed**
   - Conversational intent and natural response layers.

3. **RAG for grounded decisions**
   - Agents use retrieved context instead of raw model memory.

4. **RBAC everywhere**
   - Role-scoped access to sensitive actions and views.

5. **Trace-first operations**
   - Every important agent step produces observable evidence.

