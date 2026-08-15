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
| Company cloud activation | Firebase/Firestore integration and Cloud Run runtime identity require company IAM and one live validation | Complete company Firebase registration, service identity, worker deployment, and deployment verification |
| Reviewer decision does not yet re-run the ledger | Action is recorded and audited | Reconcile approved action into an immutable versioned ledger run |
| Worker is a polling process | Simple, inspectable assessment worker | Run as Cloud Run Job, Cloud Scheduler trigger, or managed queue consumer |
| Local JSON is the reproducible source | Prevents cloud dependency during assessment | Add validated CSV/Sheets ingestion with source snapshots |
| Sparse forecast history | The deterministic 30-day estimate is explicitly LOW confidence with five historical records | Use 12+ monthly cycles, term calendar features, calibration, and back-testing |
| Leakage findings are synthetic | Exception scanner demonstrates controls against fixture records | Ingest approved transfer, refund, adjustment, and receipt source systems |
| No outbound messaging | Required by assignment | Add a separately approved notification service with delivery audit |

## Verdict

The assessment implementation is complete and reviewable for the scoped prototype. The company Cloud Run API is deployed and its ADK agent has been live-validated with Vertex AI tool calling. Firebase/Firestore live review remains blocked only by company Firebase registration and Native Firestore activation, so it must not be presented as connected or source-of-truth until those checks pass. The remaining production improvements are explicitly outside the assessment scope.
