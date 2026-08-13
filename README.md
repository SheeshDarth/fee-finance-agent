# Fee Collection and Finance Agent

Assessment prototype for Subhanu Technologies. The workflow turns school fee records into a traceable ledger, reconciliation queue, collection worklist, review-only reminders, and an optional live Firebase dashboard.

## Deliverables

- Working source code in a public Git repository: [SheeshDarth/fee-finance-agent](https://github.com/SheeshDarth/fee-finance-agent)
- Setup and run process: this README, including Google Cloud SDK, backend, frontend, Gemini, and Firestore worker steps.
- Architecture diagram: [architecture.md](architecture.md)
- Data model and rationale: [docs/data-model.md](docs/data-model.md)
- Sample dashboard, reconciliation, worklist, and reminders: [docs/assessment-evidence.md](docs/assessment-evidence.md)
- LLM monetary safety note: [docs/llm-safety.md](docs/llm-safety.md)
- Validation record: [docs/validation.md](docs/validation.md)
- Assessment demonstration script: [docs/demo-script.md](docs/demo-script.md)
- Complete workflow and process: [docs/workflow-and-process.md](docs/workflow-and-process.md)
- Diagram set: [docs/diagrams.md](docs/diagrams.md)
- Deliverables audit: [docs/deliverables-checklist.md](docs/deliverables-checklist.md)
- Agent framework choice: [docs/agent-framework.md](docs/agent-framework.md)
- Architecture review: [docs/architecture-review.md](docs/architecture-review.md)
- Firestore security rules: [firestore.rules](firestore.rules)

## 1. Create the Project Folder

The project can live anywhere owned by the developer. This copy is at:

\`\`\`text
C:\Users\Siddharth\Desktop\Subhanu\FDE AGENT
\`\`\`

Codex is used to edit, test, document, and commit the project. The Google Cloud SDK is used for Google authentication, enabling services, and optional cloud execution. They are complementary tools.

The downloaded service-account key must stay outside Git. This repository ignores \`backend/.env\`, \`backend/service-account.json\`, and \`service-agent.json.json\`. Never paste the key into source code or commit it.

## 2. Google Cloud SDK and Firebase Setup

Run PowerShell from the repository root:

\`\`\`powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project test1-457903
gcloud services enable aiplatform.googleapis.com firestore.googleapis.com firebase.googleapis.com
\`\`\`

Create Firestore in Native Mode in the Firebase or Google Cloud console. Enable Firebase Authentication with Email/Password. Create at least one reviewer user, then create a Firestore document:

\`\`\`text
reviewers/{reviewerUid}
active: true
\`\`\`

Copy the downloaded key to \`backend/service-account.json\` only if using service-account authentication. Then:

\`\`\`powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
\`\`\`

Edit \`backend/.env\`:

\`\`\`text
GOOGLE_APPLICATION_CREDENTIALS="service-account.json"
GCP_PROJECT_ID="test1-457903"
GCP_LOCATION="us-central1"
ENABLE_LLM="false"
GEMINI_MODEL="gemini-2.5-flash"
\`\`\`

For Firebase web configuration, copy \`frontend/.env.example\` to \`frontend/.env\` and fill the values from Firebase Console > Project settings > Your apps. The frontend remains a local demo until all values exist and a signed-in reviewer is available.

## 3. Run the Deterministic Assessment Workflow

\`\`\`powershell
cd backend
.\venv\Scripts\Activate.ps1
python agent_runner.py --as-of 2026-08-13
\`\`\`

This writes \`backend/output.json\` and \`frontend/src/demo-output.json\`. The run order is:

\`\`\`text
load JSON -> reconcile payments -> calculate late fees and ledger ->
calculate plan compliance -> rank worklist using history ->
draft and validate reminders -> write audit events -> publish output
\`\`\`

Run tests and build the UI:

\`\`\`powershell
python -m unittest discover -s backend -p 'test_*.py' -v
cd ..\frontend
npm install
npm run build
npm run dev
\`\`\`

Open the Vite URL, normally \`http://127.0.0.1:5173\`. The default UI is an honest local snapshot. It does not pretend that local JSON is live Firebase data.

## 4. Live Gemini Drafting

Gemini is optional and must be explicitly enabled after Vertex AI access is configured:

\`\`\`powershell
cd backend
python agent_runner.py --as-of 2026-08-13 --llm
\`\`\`

\`backend/llm_drafter.py\` uses the Google Gen AI SDK through Vertex AI. Gemini receives the deterministic facts and returns wording only. \`validate_draft\` requires the exact ledger amount and exact due date; unknown currency values or changed dates fail validation. If the call or parse fails, the deterministic reminder template is used and the output records the fallback source.

## 5. Firestore Worker and Live Dashboard

The worker is the server-side path. It consumes \`finance_runs\` documents with status \`PENDING\`, runs the same backend workflow, writes child collections, and transitions the run to \`AWAITING_REVIEW\`, \`COMPLETE\`, or \`FAILED\`.

\`\`\`powershell
cd backend
.\venv\Scripts\Activate.ps1
python firestore_worker.py --once
\`\`\`

Remove \`--once\` for the polling worker. In the configured frontend, sign in as an active reviewer and select \`Run live workflow\`. The app subscribes to the run document plus \`student_positions\`, \`reconciliation_results\`, \`collection_worklist\`, \`reminder_drafts\`, and \`audit_events\`. Review actions are stored under \`finance_runs/{runId}/review_actions\`; the worker marks them applied and adds an audit event.

The Firebase project and web app are registered as \`test1-457903\`, and \`firestore.rules\` has been deployed. Firebase Authentication and Vertex AI still require billing to be enabled on the Google project; Google returns \`BILLING_NOT_ENABLED\` for both services until a billing account is linked. This is the only remaining console-side prerequisite before reviewer sign-in and live Gemini wording can succeed.

To clear that prerequisite, link a billing account at https://console.cloud.google.com/billing/linkedaccount?project=test1-457903, then initialize Authentication and enable Email/Password in Firebase Console > Authentication > Sign-in method. Create a reviewer account and add its UID under \`reviewers/{uid}\` with \`active: true\`. Re-run \`python firestore_worker.py --once\` and the live dashboard flow can be demonstrated.

## Money and Review Guardrails

- Every monetary calculation uses integer paise in Python.
- Late fees come from explicit policy metadata, grace days, daily rates, fixed charges, and caps.
- Only confident, non-review payments reduce verified collections and outstanding balances.
- Possible or unmatched payments remain visible as human-review items.
- Payment-plan schedules are displayed and their compliance is calculated from verified payments, not pending matches.
- Gemini cannot author ledger amounts, late fees, balances, due dates, or payment matches.
- Reminder drafts are never sent automatically.

## Assumptions and Limitations

The sample JSON is intentionally small and represents a school fee snapshot. The prototype assumes trusted fee records, a single assessment date, and a reviewer who can approve ambiguous records. It does not yet include bank-statement ingestion, CSV/Sheets import, production job scheduling, full role administration, notification delivery, or deployment to Cloud Run or Agent Runtime. The worker records reviewer decisions and audit evidence; a production implementation would also re-run the ledger against an immutable approval event and maintain a complete append-only decision history.
