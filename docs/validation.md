# Validation Record

Validated on 2026-08-13 from the repository root.

## Automated Checks

- Backend: \`python -m unittest discover -s backend -p 'test_*.py' -v\` -> 5 tests passed.
- Python syntax: every backend \`.py\` file compiled successfully.
- Frontend: \`npm run build\` -> Vite production build passed.
- Financial invariants: verified collections exclude P003/P004; net due equals collected plus outstanding; ageing overdue buckets reconcile; late fee and history score fixtures are visible.
- Live SDK imports: \`google-genai\` and \`google-cloud-firestore\` import successfully from \`backend/venv\`.
- Repository hygiene: service-account key and environment files remain ignored and untracked.
- Browser smoke: Vite served HTTP 200; desktop snapshot rendered the dashboard; mobile viewport measured `scrollWidth == clientWidth` at 390px; worklist exposed score and plan-compliance values.
- Google Cloud: project `test1-457903` authenticated with the service account; Firestore Native Mode database `(default)` in `nam5` accepted a temporary write/read/delete check.
- Firestore worker: a temporary `PENDING` run transitioned to `AWAITING_REVIEW` and published 4 positions, 5 reconciliation rows, 3 worklist rows, 2 reminder drafts, and 13 audit events; validation data was removed afterward.
- Firebase: project registration and the FeeOps Web App are complete; Firestore rules deployed successfully. Authentication initialization is blocked by `BILLING_NOT_ENABLED`.
- Vertex AI: the SDK call is wired and attempted; Gemini is blocked by the same `BILLING_NOT_ENABLED` response and the deterministic fallback passed validation.

## Live Workflow Attempt

\`python agent_runner.py --as-of 2026-08-13 --llm\` completed the run and returned the normal dashboard output. Gemini drafts fell back to deterministic templates because the local Vertex AI request did not return a usable model response. Both fallback drafts passed exact amount and due-date validation. The live Gemini integration, validation, and fallback are implemented; successful model wording still depends on the configured project, API enablement, IAM permission, and network access.

The live Firestore worker and Firebase dashboard are connected to the project. Reviewer sign-in and live Gemini wording require a linked billing account, an Email/Password provider, and an active `reviewers/{uid}` document.
