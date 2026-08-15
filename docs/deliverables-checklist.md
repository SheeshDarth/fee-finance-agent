# Deliverables Checklist

Audited against the supplied Subhanu Technologies Fee Collection & Finance Agent assignment.

| Assignment requirement | Evidence | Status |
| --- | --- | --- |
| Working source code in a Git repository with meaningful commits | Public repository and commit history at SheeshDarth/fee-finance-agent | PASS |
| README with setup and run instructions | README.md | PASS |
| Single workflow/process file | workflow-and-process.md | PASS |
| Architecture diagram | architecture.md and diagrams.md | PASS |
| Data model for fee heads, instalments, concessions, payments and rationale | data-model.md and data JSON fixtures | PASS |
| Dashboard: outstanding, collected, overdue ageing buckets, class and fee head | assessment-evidence.md and React Overview tab | PASS |
| Reconciliation with a transaction not confidently matched and flagged | P003 possible match and P004 unmatched in assessment-evidence.md | PASS |
| Collection worklist with reason for every ranking | Scored rows and plain-English reasons in evidence and React worklist | PASS |
| Two ageing-bucket reminder messages | 0-30 polite and 31-60 firm drafts in evidence and React Reminder drafts tab | PASS |
| LLM cannot invent or alter money | llm-safety.md, deterministic validator, regression test | PASS |
| Assumptions and limitations / what to build next | README limitations and validation.md | PASS |
| Multiple fee heads, instalments, partial payments, concessions, waivers, late fees | Fixture files and ledger invariants | PASS |
| Auditable reminders, waivers, plans, and approving authority | Audit events include reminder creation, WAIVER_APPROVED, PAYMENT_PLAN_APPROVED, and concession approvals | PASS |
| Google ADK 2.0 or justified equivalent | `backend/feeops_adk/agent.py`, agent-framework.md | PASS |
| Optional demo video | Not required; demo-script.md is provided instead | N/A |
| Firebase/Firestore live path | Optional code remains available but the company administrator selected a no-Firebase deployment | N/A by company deployment decision |
| Live Gemini / ADK | `feeops-backend-00007-tl4` selected evidence tools through Vertex AI in the company project; deterministic validation remains mandatory | PASS |
| Reminder sending | Explicitly not implemented per assignment rule | N/A by design |
| Production deployment, bank imports, next-month forecasting | Documented limitations; outside the 3-hour assessment scope | N/A by design |

## Verdict

The assessment deliverables are complete and evidenced. The deterministic local dashboard is the selected frontend path, and the company Cloud Run ADK agent is live-validated through Vertex AI. Firebase/Firestore is an optional legacy integration, not a company-project dependency. The local workflow remains the reproducible dashboard path.
