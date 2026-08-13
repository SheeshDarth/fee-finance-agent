# Workflow and Process

This is the single process file for running and demonstrating the assessment prototype.

## A. One-Time Setup

1. Install Google Cloud SDK, Node.js, and Python.
2. Authenticate the Google Cloud project. The canonical live-tested assessment path is `test1-457903`; the supplied company target is `intern-bnmit-july-2026` and requires the administrator actions in `docs/company-cloud-status.md` before switching this value:
   ~~~powershell
   gcloud auth login
   gcloud config set project test1-457903
   ~~~
3. Keep the service-account key at backend/service-account.json; it is ignored by Git.
4. Install backend dependencies:
   ~~~powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ~~~
5. Copy .env.example to .env and set the project, credentials, location, and model.
6. For the live-tested path, use the already registered FeeOps Web App config in `frontend/.env` and deploy rules:
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
10. Draft reminders only for overdue families with no approved plan.
11. Validate every amount and due date in reminder wording.
12. Write approval, reconciliation, position, reminder, and completion audit events.
13. Write backend/output.json and frontend/src/demo-output.json.

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
5. Audit trail: approved concessions, waiver, payment plan, reconciliations, positions, drafts, and run completion.
6. Mobile layout: wrapped navigation, stacked controls, and scroll-contained tables.

## D. Live Firestore Demonstration

For the live-tested `test1-457903` path, Blaze billing and Firebase Email/Password are already enabled. For `intern-bnmit-july-2026`, complete the company-cloud runbook first:

1. Create a reviewer account.
2. Add reviewers/{uid} with active: true.
3. Start:
   ~~~powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python firestore_worker.py
   ~~~
4. Open the dashboard and sign in.
5. Click Run live workflow.
6. Observe PENDING -> RUNNING -> AWAITING_REVIEW.
7. Use Payment review to record a reviewer action.
8. Verify review_actions/{actionId} and REVIEW_ACTION_APPLIED in the audit events.

## E. Live Gemini Demonstration

For the live-tested `test1-457903` path, Vertex AI Gemini has been exercised successfully. For the company project, create the company service account and complete IAM before running:

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
