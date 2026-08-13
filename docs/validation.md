# Validation Record

Validated on 2026-08-13 from the repository root.

## Automated Checks

- Backend: `python -m unittest discover -s backend -p 'test_*.py' -v` -> 5 tests passed.
- Python syntax: every backend `.py` file compiled successfully.
- Frontend: `npm run build` -> Vite production build passed.
- Financial invariants: verified collections exclude P003/P004; net due equals collected plus outstanding; ageing overdue buckets reconcile; late fee and history score fixtures are visible.
- Live SDK imports: `google-genai` and `google-cloud-firestore` import successfully from `backend/venv`.
- Google ADK: `google-adk 2.6.3` imports successfully; `feeops_adk` exposes the App, root agent, and two read-only tools. The ADK tool returns the deterministic `Rs. 65,835` outstanding total, 5 reconciliation rows, and 17 audit events.
- Agents CLI: `uvx google-agents-cli --version` returned `1.3.1`; deployment metadata is kept in `backend/agents-cli-manifest.yaml` and `backend/pyproject.toml`.
- Repository hygiene: service-account key and environment files remain ignored and untracked.
- Browser smoke: Vite served HTTP 200; desktop snapshot rendered the dashboard; mobile viewport measured `scrollWidth == clientWidth` at 390px; worklist exposed score and plan-compliance values.
- Google Cloud: company project `intern-bnmit-july-2026` exists, is billing-enabled, and has Vertex AI, Firestore, Cloud Run, Cloud Build, Artifact Registry, and Cloud Storage APIs enabled. The downloaded local key is still for `test1-457903` and must be replaced before company deployment.
- Firestore worker: a temporary `PENDING` run transitioned to `AWAITING_REVIEW` and published 4 positions, 5 reconciliation rows, 3 worklist rows, 2 reminder drafts, and 17 audit events; validation data was removed afterward.
- Firebase: the old `test1-457903` project registration, web app, and rules deployment were completed and tested. The company project is not yet Firebase-registered because the signed-in account lacks `projects.addFirebase` permission; this is documented in `docs/company-cloud-deployment.md`.
- Vertex AI: the SDK and ADK wrapper are wired; the company project has billing and the API enabled, but a company-project service-account key and an actual Agent Runtime deployment test remain pending.

## Live Workflow Attempt

`python agent_runner.py --as-of 2026-08-13 --llm` completed the run and returned the normal dashboard output. Gemini drafts used deterministic templates when a live model response was unavailable, and both drafts passed exact amount and due-date validation. The live Gemini integration, validation, and fallback are implemented; successful model wording depends on the company service account, IAM, and project configuration.

The Firestore worker and Firebase dashboard are live-tested against the old local project. The company project still needs the one-time Firebase registration, Native Firestore database, web app, Authentication provider, reviewer document, and company service-account key described in `docs/company-cloud-deployment.md`.
