# FeeOps Finance Agent

FeeOps is a scoped school-fee finance workflow for the Subhanu Technologies assessment. It turns fee structure, instalments, concessions, waivers, payments, payment history, and approved payment plans into a reviewable finance run. Monetary decisions remain deterministic and auditable; Gemini is limited to wording reviewed by the accounts office.

## Assessment Position

This repository is a working assessment prototype with a deterministic local path, Firebase/Firestore dashboard integration, a Google ADK wrapper, and a Cloud Run deployment path. The only intended target is the supplied company project, `intern-bnmit-july-2026`. It is not presented as a production deployment. Its current activation state and the exact administrator handoff are recorded in [docs/company-cloud-status.md](docs/company-cloud-status.md).

## Deliverables

- [Single workflow and process](docs/workflow-and-process.md)
- [Requirements-to-evidence matrix](docs/walkthrough-evidence.md)
- [Assessment evidence and sample outputs](docs/assessment-evidence.md)
- [Architecture and rendered diagrams](architecture.md) and [docs/diagrams.md](docs/diagrams.md)
- [Data model and rationale](docs/data-model.md)
- [Financial controls](docs/financial-controls.md) and [LLM safety](docs/llm-safety.md)
- [Forecasting and fee-leakage controls](docs/forecasting-and-leakage-controls.md)
- [Demo script](docs/demo-script.md)
- [Validation transcript](docs/verification-transcript.md)
- [Cloud provenance](docs/company-cloud-status.md)

## Repository Layout

```text
backend/
  agent_runner.py       deterministic end-to-end workflow
  ledger.py             integer-paise ledger, ageing, plans, worklist
  reconciliation.py     confidence-gated payment matching
  reminders.py          draft generation and validation
  llm_drafter.py        optional Vertex AI Gemini wording
  firestore_worker.py   one-shot Firestore run worker
  feeops_adk/           Google ADK read-only agent wrapper
  data/                 assessment fixtures, including instalments in fee_structure
frontend/
  src/                  React/Vite dashboard and Firebase subscriptions
docs/                   process, evidence, diagrams, controls, limitations
firestore.rules         authenticated reviewer rules
```

## Local Setup

Create or clone the repository in a normal workspace folder, for example `C:\Users\<you>\Desktop\fee-finance-agent`. Run commands from the repository root. Never commit `backend/.env`, `backend/service-account.json`, or `frontend/.env`; they are ignored.

Prerequisites: Python 3.11+, Node.js 20+, Google Cloud SDK, Firebase CLI, and optionally `uv`/`uvx` for Agents CLI.

```powershell
gcloud auth login
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
cd ..\frontend
npm install
```

Set `GCP_PROJECT_ID=intern-bnmit-july-2026` in `backend/.env`. For local cloud testing, authenticate with `gcloud auth application-default login`; for Cloud Run, attach the company runtime service account. Do not create or use a service-account JSON key. Once the company Firebase Web App exists, copy its six values into ignored `frontend/.env`.

## Run the Deterministic Workflow

From the repository root:

```powershell
.\backend\venv\Scripts\python.exe .\backend\agent_runner.py --as-of 2026-08-13
```

The run writes `backend/output.json` and `frontend/src/demo-output.json`. Expected snapshot: net due Rs. 121,335; verified collected Rs. 55,500; outstanding Rs. 65,835; overdue Rs. 47,835; late fees Rs. 1,835; and review payments P003/P004 excluded from verified collections.

## Run the Dashboard

```powershell
cd frontend
npm run dev
```

Open the Vite URL and demonstrate Overview, Payment review, Collection worklist, Reminder drafts, Forecast & controls, and Audit trail in that order. The dashboard uses local demo output when not signed in. The live Firebase path subscribes to run state and child collections with `onSnapshot` after a reviewer signs in.

## Optional Live Gemini Run

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python agent_runner.py --as-of 2026-08-13 --llm
```

This invokes Gemini through Vertex AI only for reminder wording. The ledger supplies the exact amount and due date, and `validate_draft` rejects wording that changes either value. A deterministic template is used if Gemini is unavailable. Successful live Gemini wording was verified against `test1-457903` on 2026-08-13.

## Google ADK

```powershell
cd backend
.\venv\Scripts\Activate.ps1
adk web feeops_adk
```

The ADK root agent exposes read-only tools: `run_fee_workflow`, `get_agent_decisions`, `get_escalations`, `get_cash_forecast`, `get_leakage_findings`, and `get_money_guardrail`. It cannot edit fees, approve payments, send reminders, or change ledger values. Cloud Run deployment instructions and the current company-project blocker are in [docs/company-cloud-deployment.md](docs/company-cloud-deployment.md).

## Firebase and Firestore

After the company Firebase project and Native Firestore database are activated, the worker can publish a one-shot run:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python firestore_worker.py
```

The company-project setup requires an administrator to grant Firebase registration and Firestore database permissions or perform those actions. Follow [docs/reviewer-setup.md](docs/reviewer-setup.md) after the web app and Auth provider exist.

## Tests and Verification

```powershell
python -m unittest discover -s backend -p "test_*.py" -v
cd frontend
npm run build
```

The exact results and cloud provenance are recorded in [docs/verification-transcript.md](docs/verification-transcript.md). The complete readiness judgment is in [docs/council-readiness.md](docs/council-readiness.md).

## Safety, Assumptions, and Limits

- All monetary arithmetic is integer paise; formatted rupees are presentation only.
- Only CONFIDENT reconciliations reduce verified collections. POSSIBLE and NEEDS_REVIEW payments remain visible and excluded.
- Reminders are drafts for human review. No outbound message is sent.
- Concessions, waivers, plans, and reviewer actions require recorded authority in the demo data or authenticated Firestore path.
- The prototype uses synthetic transfer, refund, and adjustment exception fixtures. It does not include production source-system ingestion, statistically validated forecasting, full duplicate/overpayment resolution, production identity governance, or a production deployment SLA.

See [docs/financial-controls.md](docs/financial-controls.md), [docs/architecture-review.md](docs/architecture-review.md), and [docs/deliverables-checklist.md](docs/deliverables-checklist.md) for the detailed rationale and remaining work.
