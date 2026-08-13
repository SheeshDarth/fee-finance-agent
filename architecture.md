# Architecture

\`\`\`mermaid
flowchart TD
  A["JSON source records"] --> B["Python finance runner"]
  B --> C["Reconciliation and confidence gate"]
  C --> D["Integer-paise ledger"]
  D --> E["Late fees, concessions, waivers, FIFO allocation"]
  E --> F["Plan compliance and history-based worklist"]
  F --> G["Gemini wording only, deterministic validation"]
  G --> H["Audit events and generated run"]
  H --> I["Local JSON snapshot"]
  H --> J["Firestore finance_runs"]
  J --> K["Firestore worker"]
  J --> L["React live subscriptions"]
  L --> M["Authenticated reviewer actions"]
  M --> J
\`\`\`

## Runtime Workflow

\`\`\`text
INGEST_DATA
  -> RECONCILE_PAYMENTS
  -> HOLD_POSSIBLE_AND_UNMATCHED_FOR_REVIEW
  -> CALCULATE_LATE_FEES
  -> APPLY_CONCESSIONS_AND_WAIVERS
  -> APPLY_CONFIDENT_PAYMENTS_FIFO
  -> CALCULATE_PLAN_COMPLIANCE
  -> SCORE_COLLECTION_WORKLIST_WITH_HISTORY
  -> DRAFT_REMINDERS
  -> VALIDATE_LLM_AMOUNT_AND_DUE_DATE
  -> WRITE_AUDIT_EVENTS
  -> PUBLISH_LOCAL_OR_FIRESTORE_RUN
\`\`\`

## Boundaries

- Python owns every financial calculation and uses integer paise.
- Reconciliation produces \`CONFIDENT\`, \`POSSIBLE\`, or \`NEEDS_REVIEW\`; only \`CONFIDENT\` reduces verified collections.
- Fee-item FIFO allocation keeps ageing and fee-head totals tied to source records.
- Late fees are derived from fee-item policies with grace days, fixed charges, daily charges, and caps.
- Payment plans contain an explicit installment schedule; compliance uses verified payment IDs and does not treat a pending match as paid.
- Historical payment behavior is joined only for explainable prioritization; it does not change the ledger balance.
- Gemini can word a reminder but cannot calculate or supply monetary truth. Amount and due date validation is mandatory.
- Firebase Authentication and Firestore rules protect reviewer reads, live-run creation, and review-action writes. The worker uses server credentials for backend processing.
- Local JSON remains the reproducible assessment path. Firestore is the live projection path when configured.

