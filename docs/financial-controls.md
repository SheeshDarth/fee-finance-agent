# Financial Controls

FeeOps treats the ledger as the source of truth. AI does not calculate, approve, post, or send money.

- **Integer arithmetic:** all calculations use paise integers. Rupee strings are formatted at the boundary.
- **Confidence gate:** only `CONFIDENT` payment matches reduce verified collections. `POSSIBLE` and `NEEDS_REVIEW` rows remain pending and visible.
- **FIFO allocation:** approved concessions, waivers, and confident payments are applied in a deterministic first-instalment-first order.
- **Late fees:** policy-derived late fees are calculated from the instalment due date and the run date; the policy result is recorded in the position trace.
- **Concessions and waivers:** they are separate adjustments with approval metadata and audit events; they do not masquerade as payments.
- **Payment plans:** the plan schedule is evaluated instalment by instalment. Missed or overdue plan instalments affect compliance and worklist reasoning.
- **History scoring:** late count, missed count, partial count, and average delay are inputs to a transparent worklist score, not hidden model output.
- **Reminder guardrail:** Gemini receives deterministic facts for wording only. The validator requires the exact ledger amount and due date and rejects changed or invented currency/date values. Drafts remain `DRAFT_FOR_REVIEW`.
- **Auditability:** reconciliation decisions, approvals, positions, reminder drafts, reviewer actions, and run completion are timestamped events.
- **No outbound side effect:** the prototype never sends a message, changes a fee, or approves a payment plan automatically.

Remaining production controls would include bank import idempotency, duplicate and overpayment handling, stronger date/source validation, role-based reviewer administration, and immutable audit storage with retention policy.
