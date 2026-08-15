# Workflow and Process

This is the single process file for running and demonstrating the assessment prototype.

## A. One-Time Setup

1. Install Google Cloud SDK, Node.js, and Python.
2. Authenticate the supplied company project, `intern-bnmit-july-2026`. Firebase registration, Native Firestore, and a Web App must exist before the live reviewer path can run:
   ~~~powershell
   gcloud auth login
   gcloud config set project intern-bnmit-july-2026
   gcloud auth application-default login
   ~~~
3. Do not create or download a service-account key. Local cloud testing uses Application Default Credentials; Cloud Run uses its attached runtime identity.
4. Install backend dependencies:
   ~~~powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ~~~
5. Copy `.env.example` to `.env` and set the company project, location, and model. Copy the company Firebase Web App values to ignored `frontend/.env`.
6. Deploy the reviewed rules after Firestore exists:
   ~~~powershell
   firebase deploy --only firestore:rules
   ~~~

## B. Deterministic Assessment Run

From the repository root:

~~~powershell
.\backend\venv\Scripts\python.exe backend\agent_runner.py --as-of 2026-08-13
~~~

The runner performs:

1. Ingest students, fee heads, term instalments, concessions, waivers, payments, payment history, and approved plans.
2. Reconcile payments into CONFIDENT, POSSIBLE, or NEEDS_REVIEW.
3. Keep possible/unmatched payments out of verified collections.
4. Calculate policy-derived late fees in integer paise.
5. Apply concessions and waivers FIFO.
6. Apply only confident payments FIFO.
7. Calculate outstanding, overdue, ageing, and fee-head totals.
8. Evaluate each approved plan's installment schedule and compliance.
9. Score the collection worklist using amount, ageing, late, partial, missed, and average-delay history.
10. Build a history-based 30-day cash-planning estimate with an explicit confidence label.
11. Scan payment, transfer, refund, adjustment, concession, receipt, and plan records for review-only leakage-control findings.
12. Route each account to a validated reminder draft, escalation, or skip action; control findings block unsafe collection contact.
13. Validate every amount and due date in reminder wording.
14. Write approval, reconciliation, forecast, control, position, reminder, decision, escalation, and completion audit events.
15. Write `backend/output.json` and `frontend/src/demo-output.json`.

## C. Dashboard Demonstration

~~~powershell
cd frontend
npm install
npm run dev
~~~

Open the displayed Vite URL and show, in order:

1. Overview: net due, verified collected, outstanding, overdue, late fees, class totals, fee-head totals, and ageing buckets.
2. Payment review: P003 possible match and P004 unmatched human-review rows.
3. Collection worklist: rank, score, history reason, and Kabir's approved-plan suppression.
4. Reminder drafts: 31-60 firm tone and 0-30 polite tone, exact due dates and amounts.
5. Forecast & controls: low-confidence 30-day estimate, likely-delay families, and exception findings routed for review.
6. Audit trail: approved concessions, waiver, payment plan, reconciliations, forecasts, control findings, decisions, drafts, and run completion.
7. Mobile layout: wrapped navigation, stacked controls, and scroll-contained tables.

## D. Live Firestore Demonstration

For `intern-bnmit-july-2026`, complete `docs/company-cloud-deployment.md` before the live run:

1. Create a reviewer account.
2. Add reviewers/{uid} with active: true.
3. Deploy the `feeops-firestore-worker` Cloud Run Job, then run it after the reviewer requests a live run:
   ~~~powershell
   gcloud run jobs execute feeops-firestore-worker --project intern-bnmit-july-2026 --region us-central1 --wait
   ~~~
4. Open the dashboard and sign in.
5. Click Run live workflow.
6. Observe PENDING -> RUNNING -> AWAITING_REVIEW.
7. Use Payment review to record a reviewer action.
8. Verify review_actions/{actionId} and REVIEW_ACTION_APPLIED in the audit events.

## E. Live Gemini Demonstration

For the company project, deploy the ADK API with an attached runtime identity that has Vertex AI User before running:

~~~powershell
cd backend
.\venv\Scripts\Activate.ps1
python agent_runner.py --llm
~~~

Gemini receives only deterministic facts for wording. It cannot set ledger values. The validator rejects any changed currency amount or due date. If Vertex AI is unavailable, the deterministic fallback remains safe and is visibly labeled.

## F. Expected Snapshot

- Net due: Rs. 121,335
- Verified collected: Rs. 55,500
- Outstanding: Rs. 65,835
- Overdue: Rs. 47,835
- Late fees: Rs. 1,835
- Pending human review: Rs. 19,000
- Ageing: 0-30 Rs. 5,285; 31-60 Rs. 13,700; 60+ Rs. 28,850
- 30-day estimate: Rs. 15,346.82, explicitly LOW confidence from five history records
- Control findings: five review-only signals; no ledger value is changed automatically
