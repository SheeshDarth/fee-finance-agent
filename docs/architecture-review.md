# Architecture Review

Reviewed against the supplied assessment requirements and the three-hour prototype constraint.

## Alignment

- Financial truth is owned by deterministic Python integer-paise calculations.
- Reconciliation confidence is a hard gate before payments affect verified collections.
- Fee-item allocation preserves traceability for ageing, late fees, and fee-head totals.
- The LLM is constrained to wording and cannot write financial state.
- Firestore is a run projection with a worker, live subscriptions, and reviewer-action collection.
- All required assessment artifacts are linked in deliverables-checklist.md.

## Risks and Boundaries

| Risk | Current treatment | Production improvement |
| --- | --- | --- |
| Billing disabled | Local fallback remains safe; exact external blocker documented | Link billing account and enable Identity Platform / Vertex AI |
| Reviewer decision does not yet re-run the ledger | Action is recorded and audited | Reconcile approved action into an immutable versioned ledger run |
| Worker is a polling process | Simple, inspectable assessment worker | Run as Cloud Run Job, Cloud Scheduler trigger, or managed queue consumer |
| Local JSON is the reproducible source | Prevents cloud dependency during assessment | Add validated CSV/Sheets ingestion with source snapshots |
| No next-month forecast | Outside required deliverables | Add a forecast model based on plan schedule and historical collections |
| No outbound messaging | Required by assignment | Add a separately approved notification service with delivery audit |

## Verdict

The assessment implementation is complete and reviewable. The only incomplete runtime capabilities are external cloud prerequisites: billing for Firebase Authentication and Vertex AI. The remaining production improvements are explicitly outside the three-hour assessment scope.

