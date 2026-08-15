# Architecture Review

Reviewed against the supplied assessment requirements and the three-hour prototype constraint.

## Alignment

- Financial truth is owned by deterministic Python integer-paise calculations.
- Reconciliation confidence is a hard gate before payments affect verified collections.
- Fee-item allocation preserves traceability for ageing, late fees, and fee-head totals.
- The LLM is constrained to wording and cannot write financial state.
- The local dashboard is a reproducible run projection. An optional Firestore worker exists but is not selected for the company deployment.
- All required assessment artifacts are linked in deliverables-checklist.md.

## Risks and Boundaries

| Risk | Current treatment | Production improvement |
| --- | --- | --- |
| Company cloud activation | The Cloud Run ADK service has a live Vertex validation; the temporary default runtime identity is broader than desired | Replace it with a least-privilege Vertex runtime identity and retain IAM-protected invocation |
| Reviewer decision does not yet re-run the ledger | Action is recorded and audited | Reconcile approved action into an immutable versioned ledger run |
| No persistent company data store | Local JSON keeps the assessment reproducible but does not create a live feed | Add immutable Cloud Storage run snapshots and a scheduled Cloud Run Job, or an approved relational store |
| Local JSON is the reproducible source | Prevents cloud dependency during assessment | Add validated CSV/Sheets ingestion with source snapshots |
| Sparse forecast history | The deterministic 30-day estimate is explicitly LOW confidence with five historical records | Use 12+ monthly cycles, term calendar features, calibration, and back-testing |
| Leakage findings are synthetic | Exception scanner demonstrates controls against fixture records | Ingest approved transfer, refund, adjustment, and receipt source systems |
| No outbound messaging | Required by assignment | Add a separately approved notification service with delivery audit |

## Verdict

The assessment implementation is complete and reviewable for the scoped prototype. The company Cloud Run API is deployed and its ADK agent has been live-validated with Vertex AI tool calling. Firebase/Firestore is deliberately not part of the company path; the local dashboard must not be presented as a live company-data feed. The remaining production improvements are explicitly outside the assessment scope.
