from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from google.adk import Agent
from google.adk.apps import App

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")
creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if creds and not os.path.isabs(creds):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((BACKEND_DIR / creds).resolve())

# ADK uses the Google Gen AI SDK. Make the company GCP deployment select
# Vertex AI explicitly so Cloud Run uses its attached service identity instead
# of falling back to the Gemini Developer API and looking for an API key.
project_id = os.getenv("GCP_PROJECT_ID", "").strip()
location = os.getenv("GCP_LOCATION", "us-central1").strip()
if project_id:
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", location)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")

from agent_runner import build_finance_run  # noqa: E402


def run_fee_workflow(as_of: str = "2026-08-13") -> str:
    """Run the deterministic fee ledger and return the auditable finance snapshot.

    Use this tool for dashboard, reconciliation, worklist, reminder, or audit questions.
    Monetary values are calculated by Python from the fixture records, not by the model.
    """
    payload = build_finance_run(date.fromisoformat(as_of), use_llm=False)
    return json.dumps({
        "asOf": payload["asOf"],
        "dashboard": payload["dashboard"],
        "reconciliationResults": payload["reconciliationResults"],
        "collectionWorklist": payload["collectionWorklist"],
        "reminderDrafts": payload["reminderDrafts"],
        "forecast": payload["forecast"],
        "leakage": payload["leakage"],
        "agentDecisions": payload["agentDecisions"],
        "escalations": payload["escalations"],
        "auditEvents": payload["auditEvents"],
    }, indent=2)


def get_agent_decisions(as_of: str = "2026-08-13") -> str:
    """Return the deterministic per-student next-action decisions for the supplied date.

    Decisions can only create a reminder draft, route a case to human review, or skip a
    settled or approved-plan case. They never send a message or alter ledger values.
    """
    payload = build_finance_run(date.fromisoformat(as_of), use_llm=False)
    return json.dumps(payload["agentDecisions"], indent=2)


def get_escalations(as_of: str = "2026-08-13") -> str:
    """Return payment, plan, and ageing cases that require a human reviewer."""
    payload = build_finance_run(date.fromisoformat(as_of), use_llm=False)
    return json.dumps(payload["escalations"], indent=2)


def get_cash_forecast(as_of: str = "2026-08-13") -> str:
    """Return the guarded 30-day cash-planning estimate and likely-delay cases.

    This is an empirical estimate based on payment history, not a promise or a
    financial target. It never writes to the ledger or changes a collection action.
    """
    payload = build_finance_run(date.fromisoformat(as_of), use_llm=False)
    return json.dumps(payload["forecast"], indent=2)


def get_leakage_findings(as_of: str = "2026-08-13") -> str:
    """Return deterministic fee-integrity exceptions for reviewer investigation.

    Findings such as an unapproved refund or post-transfer billing are signals;
    they create a human review queue and never reverse a transaction automatically.
    """
    payload = build_finance_run(date.fromisoformat(as_of), use_llm=False)
    return json.dumps(payload["leakage"], indent=2)


def get_money_guardrail() -> str:
    """Explain the non-negotiable monetary safety boundary for this agent."""
    return (
        "Python owns fee calculations, reconciliation confidence, late fees, plan compliance, "
        "and reminder amounts. The ADK/Gemini layer may summarize or word approved facts only. "
        "Every reminder draft must preserve the exact deterministic amount and due date and is "
        "review-only; this agent never sends messages."
    )


root_agent = Agent(
    name="feeops_finance_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    description="Auditable school fee collection and reconciliation assistant.",
    instruction=(
        "You are the FeeOps finance assistant. Use run_fee_workflow for every question about "
        "amounts, ageing, payment matching, worklist ranking, reminders, or audit events. "
        "Use get_agent_decisions for a family's next safe action and get_escalations for the "
        "human-review queue. Use get_cash_forecast for planning estimates and likely payment delays, "
        "and get_leakage_findings for transfers, refunds, concessions, receipts, adjustments, and plan-control exceptions. "
        "Use get_money_guardrail when asked how financial safety works. Never calculate, round, "
        "guess, or alter a monetary figure yourself. Reminders are drafts for reviewer approval "
        "only; never claim that an email, SMS, or WhatsApp message was sent. If the deterministic "
        "tool does not provide a fact, say that it is unavailable."
    ),
    tools=[
        run_fee_workflow,
        get_agent_decisions,
        get_escalations,
        get_cash_forecast,
        get_leakage_findings,
        get_money_guardrail,
    ],
)

app = App(name="feeops_adk", root_agent=root_agent)
