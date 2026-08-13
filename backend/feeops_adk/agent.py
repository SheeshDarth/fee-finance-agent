from __future__ import annotations

import json
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
        "auditEvents": payload["auditEvents"],
    }, indent=2)


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
    model="gemini-2.5-flash",
    description="Auditable school fee collection and reconciliation assistant.",
    instruction=(
        "You are the FeeOps finance assistant. Use run_fee_workflow for every question about "
        "amounts, ageing, payment matching, worklist ranking, reminders, or audit events. "
        "Use get_money_guardrail when asked how financial safety works. Never calculate, round, "
        "guess, or alter a monetary figure yourself. Reminders are drafts for reviewer approval "
        "only; never claim that an email, SMS, or WhatsApp message was sent. If the deterministic "
        "tool does not provide a fact, say that it is unavailable."
    ),
    tools=[run_fee_workflow, get_money_guardrail],
)

app = App(name="feeops_adk", root_agent=root_agent)
