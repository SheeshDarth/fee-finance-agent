# Walkthrough Evidence Matrix

Use this matrix as the evaluator-facing index. Every claim has a code path, visible output, and a repeatable action.

| Requirement | Code / document evidence | Visible result | Demo action | Status |
| --- | --- | --- | --- | --- |
| Convert business requirement into AI workflow | `backend/agent_runner.py`, `docs/workflow-and-process.md` | One run produces all finance outputs | Run deterministic command, then open Overview | DEMONSTRATED |
| Handle financial data accurately | `backend/ledger.py`, `backend/test_finance_invariants.py`, `docs/financial-controls.md` | Totals reconcile and review money is excluded | Show totals and Payment review | DEMONSTRATED |
| Clean modular software | Separate ledger, reconciliation, reminders, worker, ADK, React modules | Each concern is independently inspectable | Open repository tree and run tests | DEMONSTRATED |
| Multiple fee heads and instalments | `backend/data/fee_structure.json`, `backend/data/instalments.json` | Tuition, transport, lab and several due dates | Open data model and Overview fee-head totals | DEMONSTRATED |
| Concessions, waivers and late fees | `ledger.py`, concessions/waivers fixtures | Net due and late fees are shown with audit authority | Show Overview and Audit trail | DEMONSTRATED |
| Reconciliation with human review | `reconciliation.py` | P003 POSSIBLE and P004 NEEDS_REVIEW | Open Payment review | DEMONSTRATED |
| Collection worklist with reasons | `build_worklist` and history fixtures | Rank, score breakdown, plan compliance, reason | Open Collection worklist | DEMONSTRATED |
| Reminder messages for ageing buckets | `reminders.py`, `assessment-evidence.md` | 0-30 polite and 31-60 firm drafts | Open Reminder drafts | DEMONSTRATED |
| LLM cannot change money | `llm_drafter.py`, validator test, `docs/financial-controls.md` | Live Gemini wording passes exact amount/date gate | Run `--llm`, show validation fields | DEMONSTRATED |
| Google ADK usage | `backend/feeops_adk/agent.py` | Read-only ADK tools return deterministic workflow | Run `adk web feeops_adk` or import smoke test | DEMONSTRATED LOCALLY |
| Optional Firebase/Firestore path | `frontend/src/firebase.js`, `firestore.rules`, worker | Previously tested one-shot run and subscriptions | Do not use for the company demonstration | OPTIONAL, NOT SELECTED |
| Company GCP deployment | `backend/scripts/invoke_cloud_run_agent.ps1`, `docs/company-cloud-status.md` | Vertex-backed ADK tool calls on the private Cloud Run service | Run the PowerShell client and show the answer | DEMONSTRATED |
| Clear communication | README, diagrams, demo script, evidence pack | One canonical 5-minute narrative | Follow `docs/demo-script.md` | DEMONSTRATED |
| Production completeness | Limitations in README and architecture review | Explicit out-of-scope boundary | State limitations at close | N/A BY DESIGN |
