# Verification Transcript

Checked from the repository root and company Cloud Run on 2026-08-15.

## Local Checks

```text
python -m unittest discover -s backend -p "test_*.py" -v
11 tests passed

python -m compileall backend
all backend Python files compiled successfully

cd frontend
npm run build
Vite production build passed
```

The deterministic run returned:

```text
net due       Rs. 121,335
verified      Rs. 55,500
outstanding   Rs. 65,835
overdue       Rs. 47,835
late fees     Rs. 1,835
review rows   P003, P004
drafts        2
```

The ADK smoke check imported `feeops_adk`, exposed six read-only evidence tools, and returned outstanding Rs. 65,835, five reconciliation rows, forecasting, leakage findings, and audit events. Installed versions: `google-adk 2.6.3`, Agents CLI `1.3.1`.

## Live Checks: `test1-457903`

- `python agent_runner.py --as-of 2026-08-13 --llm`: completed successfully.
- Both reminder drafts were generated with `generationSource: GEMINI` and passed the deterministic amount/date validator.
- Firebase/Firestore worker: temporary run moved from `PENDING` to `AWAITING_REVIEW` and published 4 positions, 5 reconciliation rows, 3 worklist rows, 2 reminder drafts, and 17 audit events.
- Email/Password Identity Platform configuration: initialized and enabled.

## Company Project Checks: `intern-bnmit-july-2026`

- Project, billing, and core APIs verified.
- Agents CLI deployment dry-run generated valid Agent Runtime metadata.
- Cloud Run service `feeops-backend-00007-tl4` is Ready and IAM-protected.
- Authenticated `/list-apps` returned `feeops_adk`.
- A live `/run` invocation through Vertex AI Gemini selected `get_cash_forecast` and `get_leakage_findings`, then returned a grounded answer.
- Firebase/Firestore creation is not required: the company administrator selected the no-Firebase mode.

The exact separation between live Cloud Run capability and intentionally local dashboard/persistence boundaries is maintained in `docs/no-firebase-operating-mode.md`.
