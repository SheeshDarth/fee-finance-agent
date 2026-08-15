# FeeOps Finance Agent

FeeOps is a scoped school-fee finance workflow for the Subhanu Technologies assessment. It turns fee structure, instalments, concessions, waivers, payments, payment history, and approved payment plans into a reviewable finance run. Monetary decisions remain deterministic and auditable; Gemini is limited to wording reviewed by the accounts office.

## Assessment Position

This repository is a working assessment prototype with a deterministic local dashboard, a Google ADK wrapper, and a live Cloud Run deployment in the supplied company project, `intern-bnmit-july-2026`. Firebase/Firestore is an optional integration and is not part of the company deployment by administrator decision. The current operating path is recorded in [docs/no-firebase-operating-mode.md](docs/no-firebase-operating-mode.md).

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
- [No-Firebase operating mode](docs/no-firebase-operating-mode.md)

## Repository Layout

```text
backend/
  agent_runner.py       deterministic end-to-end workflow
  ledger.py             integer-paise ledger, ageing, plans, worklist
  reconciliation.py     confidence-gated payment matching
  reminders.py          draft generation and validation
  llm_drafter.py        optional Vertex AI Gemini wording
  firestore_worker.py   optional one-shot Firestore run worker
  feeops_adk/           Google ADK read-only agent wrapper
  data/                 assessment fixtures, including instalments in fee_structure
frontend/
  src/                  React/Vite local dashboard; optional Firebase subscriptions
docs/                   process, evidence, diagrams, controls, limitations
firestore.rules         authenticated reviewer rules
```

## Local Setup

Create or clone the repository in a normal workspace folder, for example `C:\Users\<you>\Desktop\fee-finance-agent`. Run commands from the repository root. Never commit `backend/.env`, `backend/service-account.json`, or `frontend/.env`; they are ignored.

Prerequisites: Python 3.11+, Node.js 20+, Google Cloud SDK, and optionally `uv`/`uvx` for Agents CLI. Firebase CLI is only needed for the optional legacy integration.

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

Set `GCP_PROJECT_ID=intern-bnmit-july-2026` and `GOOGLE_GENAI_USE_VERTEXAI=true` in `backend/.env`. For local cloud testing, authenticate with `gcloud auth application-default login`; Cloud Run uses its attached runtime service account. The ADK wrapper explicitly uses Vertex AI, not a Gemini API key. Do not create or use a service-account JSON key. Leave `frontend/.env` absent for the selected no-Firebase dashboard mode.

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

Open the Vite URL and demonstrate Overview, Payment review, Collection worklist, Reminder drafts, Forecast & controls, and Audit trail in that order. The selected company mode uses local deterministic output; it does not need browser credentials, Firebase, or a public finance API.

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

The ADK root agent exposes read-only tools: `run_fee_workflow`, `get_agent_decisions`, `get_escalations`, `get_cash_forecast`, `get_leakage_findings`, and `get_money_guardrail`. It cannot edit fees, approve payments, send reminders, or change ledger values. Invoke the deployed company agent with `backend/scripts/invoke_cloud_run_agent.ps1`; the complete operating path is in [docs/no-firebase-operating-mode.md](docs/no-firebase-operating-mode.md).

## Optional Firebase and Firestore Integration

This repository retains a previously tested Firebase/Firestore worker for a different environment. It is not selected for `intern-bnmit-july-2026` and is not required for the assessment demonstration. Do not register the company project solely for this prototype.

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python firestore_worker.py
```

If the organization later approves Firebase, follow [docs/reviewer-setup.md](docs/reviewer-setup.md) in an approved Firebase project; do not mix a personal Firebase project with the company Cloud Run service.

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
- Concessions, waivers, plans, and reviewer actions require recorded authority in the demo data.
- The prototype uses synthetic transfer, refund, and adjustment exception fixtures. It does not include production source-system ingestion, statistically validated forecasting, full duplicate/overpayment resolution, production identity governance, or a production deployment SLA.

See [docs/financial-controls.md](docs/financial-controls.md), [docs/architecture-review.md](docs/architecture-review.md), and [docs/deliverables-checklist.md](docs/deliverables-checklist.md) for the detailed rationale and remaining work.
