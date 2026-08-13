# Fee Collection & Finance Agent

This is a 3-hour assessment prototype for Subhanu Technologies. It converts messy school fee data into an auditable dashboard, reconciliation review list, collection worklist, and review-only reminder drafts.

## What Works

- Loads sample students, fee heads, concessions, waivers, payment plans, and payments from JSON.
- Reconciles payments using deterministic rules.
- Flags ambiguous payments for human review.
- Calculates net due, collected, outstanding, overdue, ageing buckets, class totals, fee-head totals, and payment mode totals.
- Ranks families for collection follow-up with plain-English reasons.
- Drafts reminder messages for review only.
- Validates that reminder amounts match ledger amounts.
- Writes an audit trail for every important step.
- Includes a React dashboard that reads the generated backend output.
- Includes Firestore-ready credentials/config pattern.

## Current Demo Snapshot

After running `python agent_runner.py` on August 13, 2026:

- Total outstanding: `Rs. 36,000`
- Total overdue: `Rs. 36,000`
- Payments needing human review: `P003`, `P004`
- Reminder drafts generated: `2`
- Audit events generated: `13`
- Local dashboard URL after `npm run dev`: `http://127.0.0.1:5173`

## Setup Already Done

Google Cloud SDK is installed, and the service account JSON was downloaded as:

```text
service-agent.json.json
```

The JSON key is intentionally ignored by Git. For backend use, copy or rename it to:

```text
backend/service-account.json
```

## Google Cloud Commands

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project test1-457903
gcloud services enable aiplatform.googleapis.com firestore.googleapis.com
```

Firestore should be created in Native Mode.

## Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install google-cloud-firestore google-genai python-dotenv
copy .env.example .env
python agent_runner.py
```

The local run writes:

```text
backend/output.json
```

Optional Firestore write:

```bash
python agent_runner.py --firestore
```

Only run Firestore mode after `backend/.env` points to the service account JSON.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Data Model

Core records:

- `students`
- `fee_structure`
- `concessions`
- `waivers`
- `payments`
- `payment_plans`
- generated `studentPositions`
- generated `reconciliationResults`
- generated `collectionWorklist`
- generated `reminderDrafts`
- generated `auditEvents`

All money is represented as integer paise, then formatted for display.

## Reconciliation Rules

1. Exact invoice reference maps confidently.
2. Known student ID maps confidently.
3. Narration overlap with student or guardian name becomes a possible match.
4. Missing or vague data becomes `NEEDS_REVIEW`.

The sample data includes ambiguous payments so the evaluator can see human-review behavior.

## LLM Money Safety

The LLM is not allowed to calculate fee balances. The backend computes every amount deterministically. Reminder drafting receives exact formatted values and validates generated text against those values. Unknown or invented currency values fail validation.

## Assumptions

- Sample JSON represents school records for the prototype.
- Firestore is the intended persistence and live-state broker.
- Reminder messages are drafts only and are never sent.
- Ambiguous payments require accounts-office confirmation before they affect the official ledger.

## Limitations And Next Steps

- Add CSV/Google Sheets import.
- Add authenticated reviewer roles.
- Add approval screens for reconciliation and reminders.
- Add Firestore live listeners in React after Firebase web config is complete.
- Improve payment matching with bank statement parsing and more explainable scoring.
- Deploy backend to Cloud Run or Agent Runtime after local validation.
