# FeeOps Agent Presentation Guide

Use this as the complete presentation script for the Subhanu Technologies
assessment. The recommended walkthrough is 8-10 minutes, followed by questions.

## 1. One-Minute Opening

Say:

> FeeOps is a bounded AI decision-support workflow for a school's accounts
> office. It turns fee structures, instalments, concessions, payments, payment
> history, payment plans, and control records into an auditable finance run.
> Python owns every monetary calculation in integer paise. The Google ADK agent
> uses Vertex AI to select evidence tools and explain safe next actions; it does
> not calculate money, post payments, or send messages.

Then state the problem it solves:

> The accounts office needs a trustworthy view of collection exposure, ambiguous
> bank payments, overdue families, expected short-term cash, and possible fee
> leakage. The difficult part is not merely generating a reminder; it is making
> sure no reminder or financial action bypasses evidence and review.

## 2. Pre-Demo Setup

Open three terminals from the repository root.

```powershell
# Terminal 1: prepare the reproducible baseline output
.\backend\venv\Scripts\python.exe .\backend\agent_runner.py --as-of 2026-08-13
```

```powershell
# Terminal 2: local API used by CSV/Excel uploads
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn local_api:app --host 127.0.0.1 --port 8000
```

```powershell
# Terminal 3: React dashboard
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

For the live deployed agent, keep this command ready:

```powershell
gcloud auth login
gcloud config set project intern-bnmit-july-2026
.\backend\scripts\invoke_cloud_run_agent.ps1
```

It uses your `gcloud` login to call the private Cloud Run service. It does not
need Firebase, a Gemini API key, or a service-account JSON key.

## 3. Architecture in 45 Seconds

Show `architecture.md` or `docs/diagrams.md`, then say:

1. Source records enter a deterministic Python finance engine.
2. The engine reconciles payments before the ledger can count them.
3. It calculates positions, ageing, late fees, plans, reminders, forecasts, and
   leakage-control findings.
4. A deterministic decision policy selects only three safe outcomes: draft,
   escalate, or skip.
5. The Google ADK agent on Cloud Run exposes those results as read-only tools.
   Vertex AI decides which evidence tool answers a question and writes a
   grounded explanation.
6. The local React dashboard renders the same run. CSV/Excel imports are
   processed by the local Python API immediately.

## 4. Demonstrate the Dashboard

### Overview

Show the top metrics and say:

> This is not a model estimate. These values are deterministic ledger output:
> net due is Rs. 121,335, verified collection is Rs. 55,500, outstanding is
> Rs. 65,835, overdue is Rs. 47,835, and policy-derived late fees total
> Rs. 1,835.

Point out ageing buckets, class totals, and fee-head totals. Explain that the
dashboard distinguishes verified collections from money awaiting review.

### Payment Review

Show P003 and P004.

Say:

> P003 is a possible match because the narration overlaps with Kabir Khan, but
> it has no reliable invoice reference. P004 is unmatched. Neither affects
> verified collections. The safe behavior is visible human review, not an
> optimistic ledger posting.

### Collection Worklist

Say:

> Families are not ranked only by amount. The worklist combines overdue value,
> ageing, late payments, partial payments, missed payments, and average delay.
> The reason and score breakdown are visible, so the accounts office can
> challenge a ranking. An approved and compliant plan can suppress contact.

### Reminder Drafts

Say:

> These are drafts, never sent messages. The 0-30 and 31-60 ageing buckets use
> different tone. The amount and due date originate in the ledger and are
> validated after Gemini wording. If wording changes either value, FeeOps falls
> back to a deterministic template.

### Forecast and Controls

Say:

> The 30-day forecast is Rs. 15,346.82, but it is labelled LOW confidence
> because the demo has only five historical payment records. It is planning
> evidence, not a guarantee.

Then show leakage findings:

> The controls detect an ambiguous payment, billing after transfer, an
> unapproved refund, and an unapproved manual adjustment. A finding is a review
> signal, not proof of loss, and it never reverses money automatically.

### Audit Trail

Say:

> Every significant workflow event is recorded: approvals, reconciliation
> results, calculated positions, forecast, findings, decisions, reminder drafts,
> escalations, and completion. This makes the outcome explainable after the
> fact.

## 5. Demonstrate an Upload

Click **Upload data** and choose either `frontend/public/template.xlsx` or a
payment CSV. A quick payment CSV example is:

```text
paymentId,studentId,invoiceRef,date,amountPaise,mode,rawNarration
P-LOCAL-001,S001,F001,2026-08-01,2000000,UPI,LOCAL IMPORT
```

Say:

> The file is parsed locally, validated, merged with the supporting fixture
> datasets, and sent to the same Python ledger used by the agent. The browser
> receives a complete new finance run immediately. It does not wait for a
> Firestore polling worker, and it does not mutate the original fixture files.

Show that the metric values change. Then click **Reset snapshot** to restore the
baseline.

If asked about money format, say:

> `amountPaise` is integer paise. `2000000` is Rs. 20,000. Fractional paise are
> rejected; the importer does not round or truncate financial values.

## 6. Demonstrate the Live Agent

Run:

```powershell
.\backend\scripts\invoke_cloud_run_agent.ps1 -Prompt "Use the agent decisions and escalation tools. What is the safest next action for the highest-risk case, and why?"
```

Say:

> This call goes to the private FeeOps Cloud Run service in
> `intern-bnmit-july-2026`. It uses an IAM identity token from `gcloud`. Gemini
> uses the ADK tools rather than free-form guessing and returns a grounded
> answer. In the current run, P004 is escalated because it cannot be confidently
> matched to an invoice or student.

Then state why this is agentic:

> The LLM is not being used as a calculator. It is acting as a bounded tool
> user: it chooses among ledger, decision, escalation, forecast, leakage, and
> safety tools; receives structured evidence; and explains the safe action. The
> deterministic workflow controls the allowed actions and the human-review
> boundary.

## 7. Current Deployment Status

Use these exact claims:

- The Google ADK backend is deployed on private Cloud Run in
  `intern-bnmit-july-2026`.
- Vertex AI Gemini tool calling has been live-validated on that service.
- The dashboard is intentionally local and reproducible.
- Firebase registration is not part of the company deployment.
- Current source data is versioned local fixture data, plus temporary local
  CSV/Excel imports. It is not a live Firestore or production school database.
- There is no automatic outbound messaging or autonomous money movement.

## 8. Important Limitations

State these voluntarily near the end:

> This is a strong scoped assessment prototype, not a production financial
> platform. It does not yet have a persistent company data store, bank-feed
> ingestion, production authentication for reviewers, a scheduler, or a live
> company-data dashboard. The forecast is explicitly low confidence because the
> sample history is sparse. Those limits are intentional and documented.

If asked what comes next:

1. Use Native Firestore, Cloud Storage snapshots, or Cloud SQL inside the
   company GCP project as the persistent source of truth.
2. Run a Cloud Run Job on a schedule to build immutable daily runs.
3. Add a secured browser-to-backend layer for authenticated reviewers.
4. Add validated bank imports, duplicate/overpayment handling, and approved
   notification delivery with audit records.
5. Use more historical terms and back-testing before relying on forecasts for
   budgeting.

## 9. Likely Questions and Answers

**Why use AI if Python can run the workflow?**

> Python is right for monetary truth. AI adds value by choosing evidence tools,
> explaining exceptions, answering finance questions in context, and drafting
> constrained communication. The design deliberately keeps the model outside
> monetary authority.

**Can Gemini invent an amount?**

> No monetary output comes from Gemini. The ledger supplies the amount and due
> date; `validate_draft` rejects any wording that changes them. The agent tools
> return deterministic values only.

**Why is P004 not counted as collected?**

> It has no trustworthy invoice, student ID, or narration match. Counting it
> would overstate collection performance, so it is escalated for human review.

**Why does the import run locally?**

> The administrator selected a no-Firebase deployment. The local API makes the
> upload demo fast and reproducible while using the same tested Python workflow.
> A persistent company data store is a clear next production step.

**Does the agent send reminders?**

> No. It creates validated drafts only. Human review and an approved delivery
> channel would be required before any real parent communication.

## 10. Claims to Avoid

Do not say:

- “The dashboard is connected to live company Firestore data.”
- “The agent automatically collects money or sends parent messages.”
- “The forecast is statistically reliable or a budget commitment.”
- “A leakage finding proves fraud or loss.”
- “The separate `test1-457903` Firebase project is the company data store.”

## 11. Close in 20 Seconds

Say:

> The core achievement is not using an LLM for arithmetic. It is combining a
> deterministic financial engine with a bounded ADK agent that can investigate,
> explain, draft, and escalate without bypassing accounting controls. The
> workflow is modular, demonstrable, and ready for a company-owned persistence
> layer when that scope is approved.
