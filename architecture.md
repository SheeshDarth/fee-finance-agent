# Architecture

```text
React dashboard
  |
  | local demo reads backend/output.json
  | Firestore-ready version creates finance_runs/PENDING
  v
Firestore reactive broker
  |
  | Python on_snapshot / batch run
  v
Fee finance agent
  |
  | deterministic code only
  v
Ledger + reconciliation engine
  |
  | exact integer-paise values
  v
Reminder drafter
  |
  | review-only wording; amounts validated
  v
Dashboard, worklist, reminder drafts, audit trail
```

## Design Rationale

- The Python backend owns all financial calculations.
- Currency is stored as integer paise to avoid floating-point errors.
- Reconciliation is rule-based with confidence levels and reasons.
- Ambiguous payments are not silently applied; they are marked for human review.
- The reminder drafter is a controlled assistant. It can word a message, but it cannot compute or invent amounts.
- Audit events make every recommendation traceable.
- Firestore is prepared as the live state broker, but the local JSON demo works without cloud connectivity.

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

