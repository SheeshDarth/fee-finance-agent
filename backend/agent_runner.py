from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        return False

from ledger import build_worklist, calculate_positions
from reconciliation import reconcile_payments
from reminders import draft_reminders
from seed_data import load_seed_data, write_output


BASE_DIR = Path(__file__).resolve().parent


def audit_event(event_type: str, details: dict[str, Any], actor: str = "fee-agent-runner") -> dict[str, Any]:
    return {
        "eventType": event_type,
        "actor": actor,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details,
    }


def build_finance_run(as_of: date | None = None, use_llm: bool = False) -> dict[str, Any]:
    as_of = as_of or date.today()
    data = load_seed_data()
    events = [audit_event("FINANCE_RUN_STARTED", {"asOf": as_of.isoformat()})]

    reconciliation_results = reconcile_payments(
        data["students"], data["fee_items"], data["payments"]
    )
    for result in reconciliation_results:
        event_type = "PAYMENT_RECONCILED"
        if result["requiresHumanReview"]:
            event_type = "PAYMENT_REQUIRES_REVIEW"
        events.append(audit_event(event_type, result))

    positions, dashboard = calculate_positions(
        students=data["students"],
        fee_items=data["fee_items"],
        concessions=data["concessions"],
        waivers=data["waivers"],
        payments=data["payments"],
        payment_plans=data["payment_plans"],
        payment_history=data["payment_history"],
        reconciliation_results=reconciliation_results,
        as_of=as_of,
    )
    for position in positions:
        events.append(audit_event("STUDENT_POSITION_CALCULATED", {
            "studentId": position["studentId"],
            "outstandingPaise": position["outstandingPaise"],
            "trace": position["trace"],
        }))

    worklist = build_worklist(positions)
    reminder_drafts = draft_reminders(positions, use_llm=use_llm)
    for draft in reminder_drafts:
        events.append(audit_event("REMINDER_DRAFT_CREATED", {
            "studentId": draft["studentId"],
            "status": draft["status"],
            "validationPassed": draft["validationPassed"],
        }))

    events.append(audit_event("FINANCE_RUN_COMPLETED", {
        "studentCount": len(data["students"]),
        "reconciliationCount": len(reconciliation_results),
        "draftCount": len(reminder_drafts),
    }))

    return {
        "status": "COMPLETE",
        "asOf": as_of.isoformat(),
        "dashboard": dashboard,
        "studentPositions": positions,
        "reconciliationResults": reconciliation_results,
        "collectionWorklist": worklist,
        "reminderDrafts": reminder_drafts,
        "auditEvents": events,
        "notes": {
            "moneyGuardrail": "All amounts are derived by deterministic Python code using integer paise. The reminder generator is allowed to word messages only.",
            "demoMode": "Local JSON seed data is the default so the assessment demo does not depend on cloud connectivity.",
            "llmMode": "Gemini is optional; when enabled it can word reminders only, and deterministic validation rejects changed amounts or due dates.",
        },
    }


def maybe_write_firestore(payload: dict[str, Any]) -> None:
    load_dotenv(BASE_DIR / ".env")
    project_id = os.getenv("GCP_PROJECT_ID")
    credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not project_id or not credentials:
        print("Skipping Firestore write: GCP_PROJECT_ID or GOOGLE_APPLICATION_CREDENTIALS missing.")
        return

    from google.cloud import firestore

    db = firestore.Client(project=project_id)
    run_ref = db.collection("finance_runs").document()
    run_ref.set({
        "status": payload["status"],
        "asOf": payload["asOf"],
        "dashboard": payload["dashboard"],
        "createdAt": datetime.now(timezone.utc).isoformat(),
    })
    for name, rows in [
        ("student_positions", payload["studentPositions"]),
        ("reconciliation_results", payload["reconciliationResults"]),
        ("collection_worklist", payload["collectionWorklist"]),
        ("reminder_drafts", payload["reminderDrafts"]),
        ("audit_events", payload["auditEvents"]),
    ]:
        for row in rows:
            run_ref.collection(name).add(row)
    print(f"Wrote Firestore finance run: {run_ref.id}")


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    parser = argparse.ArgumentParser(description="Run the Fee Collection & Finance Agent demo.")
    parser.add_argument("--as-of", default="2026-08-13", help="Assessment date in YYYY-MM-DD format.")
    parser.add_argument("--firestore", action="store_true", help="Also write output to Firestore using backend/.env.")
    parser.add_argument("--llm", action="store_true", help="Use Vertex AI Gemini for reminder wording, with deterministic fallback and validation.")
    args = parser.parse_args()

    use_llm = args.llm or os.getenv("ENABLE_LLM", "false").lower() == "true"
    payload = build_finance_run(datetime.strptime(args.as_of, "%Y-%m-%d").date(), use_llm=use_llm)
    output_path = write_output(payload)
    frontend_demo_path = BASE_DIR.parent / "frontend" / "src" / "demo-output.json"
    if frontend_demo_path.parent.exists():
        write_output(payload, frontend_demo_path)
    print(json.dumps({
        "status": payload["status"],
        "asOf": payload["asOf"],
        "output": str(output_path),
        "frontendDemoOutput": str(frontend_demo_path),
        "totalOutstanding": payload["dashboard"]["totalOutstanding"],
        "totalOverdue": payload["dashboard"]["totalOverdue"],
        "reviewPayments": [
            item["paymentId"] for item in payload["reconciliationResults"] if item["requiresHumanReview"]
        ],
        "draftCount": len(payload["reminderDrafts"]),
    }, indent=2))

    if args.firestore:
        maybe_write_firestore(payload)


if __name__ == "__main__":
    main()
