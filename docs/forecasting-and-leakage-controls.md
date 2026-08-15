# Forecasting and Fee-Leakage Controls

## Purpose

This extension makes FeeOps proactive without allowing a model to alter money.
It adapts the useful architectural concepts from
[PayGuard-AgentX](https://github.com/SheeshDarth/PayGuard-AgentX): deterministic
data-quality tools, planning output, evidence-led findings, and human approval.
It does not copy that project's LangGraph, local-LLM, graph, vector, or fraud
stack. FeeOps remains a Google ADK and Vertex AI project.

## Cash forecasting tool

`backend/forecasting.py` produces a 30-day planning estimate from the current
verified position and payment history.

1. It includes only outstanding fee items due on or before the forecast horizon.
2. It calculates historical recovery from integer-paise expected and paid values.
3. It blends each student's sparse history with a global history prior, preventing
   a single payment from becoming a 0% or 100% certainty claim.
4. It applies a deterministic timing adjustment for missed, partial, or late
   payments.
5. It returns expected cash inflow, expected outstanding, projected collection
   rate, and likely-delay students.

The output is explicitly labelled `LOW` confidence for the supplied fixture,
which has only five history records. It is a planning estimate, not a prediction
guarantee, annual budget, collection target, or ledger entry.

## Leakage-control tool

`backend/leakage.py` is a deterministic exception scanner. It never changes a
fee, payment, refund, concession, adjustment, or plan. It returns reviewer
findings for:

- unresolved or unallocated payments;
- unapproved or duplicate concessions;
- concessions exceeding recorded fee items;
- payment plans whose instalments do not equal the approved total;
- billing after a completed transfer;
- unapproved refunds or refunds greater than their receipt;
- unapproved manual adjustments; and
- likely duplicate receipts with identical student, date, amount, mode, and narration.

The synthetic fixture deliberately demonstrates five signals: P003/P004 remain
unreconciled; S004 has post-transfer billing; R001 lacks refund authority; and
A001 lacks adjustment authority. These are exception signals, not proven losses.

## Agentic workflow

~~~mermaid
flowchart TD
  Run[Finance run requested] --> Ledger[Deterministic reconciliation and ledger]
  Ledger --> Forecast[Forecasting tool]
  Ledger --> Controls[Leakage-control tool]
  Forecast --> Supervisor[ADK agent and bounded decision policy]
  Controls --> Supervisor
  Supervisor -->|safe overdue case| Draft[Validated reminder draft]
  Supervisor -->|payment or control exception| Queue[Firestore human-review queue]
  Draft --> Review[Reviewer approval]
  Queue --> Review
  Review --> Audit[Immutable-style audit event trail]
~~~

The ADK agent can answer questions through `get_cash_forecast` and
`get_leakage_findings`. The deterministic policy may draft, escalate, or skip;
it cannot send a message or commit a financial correction. An unresolved control
finding blocks collection contact for that family.

## Production next steps

- Use at least 12 monthly cycles and calendar/term features before raising
  forecast confidence or using the model for budgeting.
- Ingest approved transfer, refund, and adjustment source systems rather than
  synthetic JSON.
- Make reviewer resolution create a linked case outcome and rerun the immutable
  position calculation; do not edit historical audit events.
- Add calibrated forecast back-testing and false-positive metrics before using
  findings as operational performance measures.
