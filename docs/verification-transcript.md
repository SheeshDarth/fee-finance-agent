# Verification Transcript

Checked from the repository root on 2026-08-13.

## Local Checks

```text
python -m unittest discover -s backend -p "test_*.py" -v
7 tests passed

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

The ADK smoke check imported `feeops_adk`, exposed `run_fee_workflow` and `get_money_guardrail`, and returned outstanding Rs. 65,835, five reconciliation rows, and 17 audit events. Installed versions: `google-adk 2.6.3`, Agents CLI `1.3.1`.

## Live Checks: `test1-457903`

- `python agent_runner.py --as-of 2026-08-13 --llm`: completed successfully.
- Both reminder drafts were generated with `generationSource: GEMINI` and passed the deterministic amount/date validator.
- Firebase/Firestore worker: temporary run moved from `PENDING` to `AWAITING_REVIEW` and published 4 positions, 5 reconciliation rows, 3 worklist rows, 2 reminder drafts, and 17 audit events.
- Email/Password Identity Platform configuration: initialized and enabled.

## Company Project Checks: `intern-bnmit-july-2026`

- Project, billing, and core APIs verified.
- Agents CLI deployment dry-run generated valid Agent Runtime metadata.
- Actual deployment was not claimed: local ADC was unavailable and Firebase/Firestore creation returned permission denied for the current identity.

The exact separation between live-tested and pending company work is maintained in `docs/company-cloud-status.md`.
