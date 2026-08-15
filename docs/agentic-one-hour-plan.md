# One-Hour Agentic Upgrade Plan (Assignment-Aligned)

Time-boxed plan to add real agentic behaviour **within the Subhanu Fee Collection & Finance
Agent constraints**. Scope is chosen to *deepen deliverables already in the brief*, not to add
capability the brief did not ask for. The full, beyond-scope vision (mandates, signed receipts,
consensus, memory) stays in [agentic-roadmap.md](agentic-roadmap.md) and is surfaced only as
"what I'd build next".

## Constraint check first (why this scope)

The brief is explicit: **"Correctness of money matters more than AI sophistication"**, reminders
are **draft-only**, ambiguous payments must be **flagged for human review**, and the
"What Not To Do" list warns against **over-engineering**. Therefore:

- **In the hour:** an *explainable per-case decision + escalation layer* that strengthens the
  required worklist, human-review, audit-trail, and ADK deliverables.
- **Deferred to "next steps":** Active Mandates, cryptographic/HMAC signed receipts, multi-agent
  consensus, cross-run memory. These are legitimate but **beyond the 3-hour brief** and would
  add AI sophistication the rubric deprioritises. They are documented in `agentic-roadmap.md`.

## Achievable in one hour? Yes.

Because it reuses the deterministic outputs already produced by `agent_runner.py`
(`collectionWorklist`, `reminderDrafts`, `reconciliationResults`, `auditEvents`) and adds a thin
decision layer on top. No new dependencies, no crypto, no schema rewrite.

## In scope (the hour)

- `agent_runner.py` — add an **`agentDecisions`** step: for each worklisted student the agent
  chooses one action — `DRAFT_REMINDER` / `ESCALATE_FOR_REVIEW` / `SKIP_PAID_OR_PLAN` — from
  **deterministic** signals (ageing bucket, outstanding, `hasApprovedPaymentPlan`/paid,
  reconciliation review flags, history), each with a plain-English `reason`.
- `agent_runner.py` — emit an **`escalations`** list and new audit events
  (`CASE_ESCALATED_FOR_REVIEW`, `REMINDER_DECISION_MADE`) reusing the existing audit-event shape.
- `feeops_adk/agent.py` — add **read-only** ADK tools `get_agent_decisions()` and
  `get_escalations()`; extend the instruction. (Boundary unchanged: still read/draft only.)
- Output wiring — write `agentDecisions` + `escalations` into `output.json` and
  `frontend/src/demo-output.json` (optional small dashboard note).
- Tests — money-unchanged invariant + "every decision has a reason" + "paid/plan excluded".

## Hard constraints honoured (unchanged)

1. Integer paise only; no float. The LLM never computes or alters a monetary value — the
   decision is **deterministic**; the LLM still only words reminders (existing `validate_draft`).
2. Reminders remain `DRAFT_FOR_REVIEW`. No live email/SMS/WhatsApp sending.
3. Ambiguous payments stay **visible and flagged** for human review — never hidden or auto-cleared.
4. No parent-facing amount unless traceable to source records.
5. No over-engineering: no new auth model, no crypto, no parallel system in the hour.

## Maps to expected deliverables

| New feature | Required deliverable it strengthens |
|---|---|
| `agentDecisions` per student with a reason | "Prioritized collection worklist with a reason for every ranking" + "avoid drafting reminders for paid / approved-plan families" |
| `escalations` + `CASE_ESCALATED_FOR_REVIEW` audit event | "Reconciliation … flagged for human review" + "audit trail for reminders, waivers, plans, approvals" |
| Read-only `get_agent_decisions` / `get_escalations` ADK tools | "Google ADK 2.0 or justified equivalent" |
| Money-unchanged regression test | "LLM cannot invent or alter money" |
| PayGuard concepts written as next steps | "Assumptions and limitations / what to build next" |

## Time budget (60 min)

| Time | Step | Output |
|---|---|---|
| 0:00–0:20 | `agent_runner.py`: build `agentDecisions` from the existing worklist + positions — deterministic action + `reason` per row; exclude paid/approved-plan; escalate review-flagged and `60+` cases | explainable per-case decisions |
| 0:20–0:35 | Emit `escalations` list + `CASE_ESCALATED_FOR_REVIEW` / `REMINDER_DECISION_MADE` audit events; write to `output.json` + `frontend/src/demo-output.json` | enriched audit trail + run output |
| 0:35–0:50 | `feeops_adk/agent.py`: add read-only `get_agent_decisions()`, `get_escalations()`; update instruction to use them; keep the money guardrail | deeper ADK surface, same boundary |
| 0:50–1:00 | Extend `test_finance_invariants.py` (totals unchanged) + add decision tests (reason present, paid/plan excluded); run `python -m unittest discover -s backend -p "test_*.py"` | green tests, money identical |

## Demo / "done" check

```powershell
.\backend\venv\Scripts\python.exe .\backend\agent_runner.py --as-of 2026-08-13
```

Confirm `output.json` now has `agentDecisions` (DRAFT vs ESCALATE vs SKIP, each with a reason)
and an `escalations` list with matching audit events — while the money figures are **identical**
to before (net due Rs. 121,335; verified collected Rs. 55,500; outstanding Rs. 65,835; overdue
Rs. 47,835; late fees Rs. 1,835). That is a real agentic upgrade that *reinforces* the rubric
instead of fighting it.

## Walkthrough line (for the reserved 15 min)

"The agent now makes an explainable per-case decision — draft, escalate, or skip — and routes
ambiguity to human review, deepening the worklist and audit deliverables. Money stays
deterministic and reminders stay draft-only. Cryptographic mandates/receipts and multi-agent
consensus are deliberately out of the 3-hour scope and are written up as next steps in
`agentic-roadmap.md`."

## If time runs short (fallback order)

Drop the ADK tools and dashboard note first, then the tests. Minimum viable win:
`agentDecisions` + `escalations` + audit events in `output.json`, money unchanged.
