# Architecture

```text
Local JSON inputs
  |
  | Python batch run (default demo path)
  v
Fee finance runner
  |
  | deterministic code only
  v
Ledger + reconciliation engine
  |
  | exact integer-paise values
  v
Worklist + template reminder drafter
  |
  | review-only wording; amounts validated
  v
Generated output.json + audit trail
  |
  | React reads frontend/src/demo-output.json
  v
Accounts-office dashboard

Optional path: `python agent_runner.py --firestore` writes the generated run and
child collections to Firestore. It is a one-shot writer in this prototype; the
React app does not yet listen to Firestore in real time.
```

## Design Rationale

- The Python backend owns all financial calculations.
- Currency is stored as integer paise to avoid floating-point errors.
- Reconciliation is rule-based with confidence levels and reasons.
- Ambiguous payments are not applied to verified collections; they are marked for human review.
- Reminder drafting is deterministic templating in this prototype. It can word a message, but it cannot compute or invent amounts.
- Audit events make every recommendation traceable.
- Fee-item FIFO allocation keeps ageing and fee-head totals tied to individual billing items.
- Firestore is an optional persistence path, not the default live state broker.

## Workflow

```text
INGEST_DATA
  -> RECONCILE_PAYMENTS
  -> CALCULATE_LEDGER
  -> BUILD_DASHBOARD_METRICS
  -> RANK_COLLECTION_WORKLIST
  -> DRAFT_REMINDERS
  -> WRITE_AUDIT_EVENTS
  -> COMPLETE
```
