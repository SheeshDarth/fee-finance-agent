# Data Model and Rationale

All money fields ending in \`Paise\` are integer minor units. Formatted \`Rs.\` fields are derived display values and are never used for calculations.

| Record | Key fields | Rationale |
| --- | --- | --- |
| \`students\` | \`studentId\`, name, class, guardian | Stable identity and safe recipient context. |
| \`fee_structure\` | \`feeItemId\`, \`studentId\`, \`feeHead\`, term, \`instalmentId\`, due date, amount, \`lateFeePolicy\` | Item-level billing makes FIFO allocation, ageing, fee-head totals, instalments, and late fees auditable. |
| \`concessions\` | \`concessionId\`, student, amount, reason | Student-level reductions are traceable and allocated before payments. |
| \`waivers\` | \`waiverId\`, student, amount, reason | Separate from concessions because a waiver has a different approval meaning. |
| \`payments\` | \`paymentId\`, amount, mode, date, narration, optional invoice | Raw bank or cash evidence is preserved before matching. |
| \`payment_history\` | student, due date, paid date, expected/paid amount, status, days late | Historical behavior is separate from current ledger money and feeds explainable worklist scoring. |
| \`payment_plans\` | plan approval metadata, total, ordered \`installments\` with due date, amount, paid, status, payment IDs | The schedule is explicit so the system can distinguish an approved plan from actual compliance. |
| generated position | fee items, verified paid, outstanding, overdue, late fee, plan compliance, history summary, trace IDs | One student-level view for dashboard and reviewers. |
| generated run | status, dashboard, child collections, audit events | Firestore is a run-oriented live projection, while source JSON remains the deterministic demo input. |

## Calculation Order

1. Apply late-fee policy to each fee item as of the run date.
2. Apply concession and waiver adjustments FIFO by due date.
3. Apply only confident reconciled payments FIFO by due date.
4. Calculate outstanding, overdue, and ageing buckets per fee item.
5. Calculate payment-plan installment compliance using verified payment IDs.
6. Join historical behavior for score components and human-readable reasons.

