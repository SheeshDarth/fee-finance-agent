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
from forecasting import build_cash_forecast
from leakage import detect_fee_leakage
from reconciliation import reconcile_payments
from reminders import draft_reminders
from data_import import merge_import_data
from seed_data import load_seed_data, write_output


BASE_DIR = Path(__file__).resolve().parent


def audit_event(event_type: str, details: dict[str, Any], actor: str = "fee-agent-runner") -> dict[str, Any]:
    return {
        "eventType": event_type,
        "actor": actor,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details,
    }


def build_agent_decisions(
    positions: list[dict[str, Any]],
    reconciliation_results: list[dict[str, Any]],
    leakage_findings: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Choose the next safe workflow action from deterministic finance facts.

    Decisions route cases to a draft or a human queue only. They do not change the
    ledger, approve a payment, or send a parent-facing message.
    """
    review_payments = [row for row in reconciliation_results if row.get("requiresHumanReview")]
    reviews_by_student: dict[str, list[dict[str, Any]]] = {}
    leakage_by_student: dict[str, list[dict[str, Any]]] = {}
    escalations: list[dict[str, Any]] = []

    for payment in review_payments:
        student_id = payment.get("matchedStudentId")
        if student_id:
            reviews_by_student.setdefault(student_id, []).append(payment)
        escalations.append({
            "escalationId": f"PAYMENT-{payment['paymentId']}",
            "targetType": "PAYMENT",
            "targetId": payment["paymentId"],
            "studentId": student_id,
            "priority": "HIGH" if payment["confidence"] == "NEEDS_REVIEW" else "MEDIUM",
            "status": "PENDING_HUMAN_REVIEW",
                "reason": f"{payment['paymentId']} is {payment['confidence']} and cannot reduce verified collections until a reviewer confirms it. {payment['reason']}",
        })

    for finding in leakage_findings:
        student_id = finding.get("studentId")
        if student_id:
            leakage_by_student.setdefault(student_id, []).append(finding)
        if finding["category"] != "UNRECONCILED_PAYMENT":
            escalations.append({
                "escalationId": finding["findingId"],
                "targetType": "CONTROL_FINDING",
                "targetId": finding["findingId"],
                "studentId": student_id,
                "priority": finding["severity"],
                "status": "PENDING_HUMAN_REVIEW",
                "reason": finding["reason"],
            })

    decisions: list[dict[str, Any]] = []
    for position in positions:
        student_id = position["studentId"]
        pending_reviews = reviews_by_student.get(student_id, [])
        high_leakage = [row for row in leakage_by_student.get(student_id, []) if row["severity"] == "HIGH" and row["category"] != "UNRECONCILED_PAYMENT"]
        decision = {
            "studentId": student_id,
            "studentName": position["studentName"],
            "ageingBucket": position["ageingBucket"],
            "outstandingPaise": position["outstandingPaise"],
            "outstanding": position["outstanding"],
            "requiresHumanReview": False,
            "relatedPaymentIds": [payment["paymentId"] for payment in pending_reviews],
        }

        if high_leakage:
            finding = high_leakage[0]
            decision.update({
                "chosenAction": "ESCALATE_FOR_REVIEW",
                "requiresHumanReview": True,
                "relatedControlFindingIds": [row["findingId"] for row in high_leakage],
                "reason": f"{finding['category'].replace('_', ' ').title()} requires a finance-control review. Collection contact and record changes remain blocked until it is resolved.",
            })
        elif position["outstandingPaise"] <= 0:
            decision.update({
                "chosenAction": "SKIP_PAID_OR_PLAN",
                "reason": "No outstanding balance remains, so no reminder or collection action is appropriate.",
            })
        elif pending_reviews:
            decision.update({
                "chosenAction": "ESCALATE_FOR_REVIEW",
                "requiresHumanReview": True,
                "reason": f"Payment {pending_reviews[0]['paymentId']} requires reconciliation review. No reminder is advanced until that evidence is resolved.",
            })
        elif position["hasApprovedPaymentPlan"]:
            if position["planCompliance"] == "OVERDUE":
                decision.update({
                    "chosenAction": "ESCALATE_FOR_REVIEW",
                    "requiresHumanReview": True,
                    "reason": "An approved payment plan is overdue. Escalate to the accounts office for plan review; do not draft a parent reminder.",
                })
                escalations.append({
                    "escalationId": f"PLAN-{student_id}",
                    "targetType": "STUDENT",
                    "targetId": student_id,
                    "studentId": student_id,
                    "priority": "HIGH",
                    "status": "PENDING_HUMAN_REVIEW",
                    "reason": "The approved payment-plan schedule is overdue. A reviewer must decide the next step before any parent contact.",
                })
            else:
                decision.update({
                    "chosenAction": "SKIP_PAID_OR_PLAN",
                    "reason": "An approved payment plan is on track, so the case is intentionally excluded from reminder drafting.",
                })
        elif position["ageingBucket"] == "60+":
            decision.update({
                "chosenAction": "ESCALATE_FOR_REVIEW",
                "requiresHumanReview": True,
                "reason": "The balance is more than 60 days overdue. Escalate for an accounts-office decision instead of creating an automatic reminder draft.",
            })
            escalations.append({
                "escalationId": f"AGEING-{student_id}",
                "targetType": "STUDENT",
                "targetId": student_id,
                "studentId": student_id,
                "priority": "HIGH",
                "status": "PENDING_HUMAN_REVIEW",
                "reason": "This account is in the 60+ ageing bucket and needs an accounts-office decision before further collection action.",
            })
        elif position["shouldDraftReminder"]:
            decision.update({
                "chosenAction": "DRAFT_REMINDER",
                "reason": f"The balance is overdue in the {position['ageingBucket']} bucket, has no approved plan, and has no unresolved payment match. A validated draft is ready for human review.",
            })
        else:
            decision.update({
                "chosenAction": "SKIP_PAID_OR_PLAN",
                "reason": "There is no eligible overdue balance for a reminder draft at this time.",
            })
        decisions.append(decision)

    return decisions, escalations


def build_finance_run(as_of: date | None = None, use_llm: bool = False, override_data: dict[str, Any] | None = None) -> dict[str, Any]:
    as_of = as_of or date.today()
    data = merge_import_data(override_data) if override_data is not None else load_seed_data()
    events = [audit_event("FINANCE_RUN_STARTED", {"asOf": as_of.isoformat()})]
    for concession in data["concessions"]:
        events.append(audit_event("CONCESSION_APPROVED", concession, actor=concession.get("approvedBy", "fee-agent-runner")))
    for waiver in data["waivers"]:
        events.append(audit_event("WAIVER_APPROVED", waiver, actor=waiver.get("approvedBy", "fee-agent-runner")))
    for plan in data["payment_plans"]:
        if plan.get("status") == "APPROVED":
            events.append(audit_event("PAYMENT_PLAN_APPROVED", plan, actor=plan.get("approvedBy", "fee-agent-runner")))

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

    forecast = build_cash_forecast(positions, data["payment_history"], dashboard, as_of)
    leakage = detect_fee_leakage(data, reconciliation_results, positions, as_of)
    agent_decisions, escalations = build_agent_decisions(positions, reconciliation_results, leakage["findings"])
    worklist = build_worklist(positions)
    decision_by_student = {row["studentId"]: row for row in agent_decisions}
    eligible_positions = [
        position for position in positions
        if decision_by_student[position["studentId"]]["chosenAction"] == "DRAFT_REMINDER"
    ]
    reminder_drafts = draft_reminders(eligible_positions, use_llm=use_llm)
    for draft in reminder_drafts:
        events.append(audit_event("REMINDER_DRAFT_CREATED", {
            "studentId": draft["studentId"],
            "status": draft["status"],
            "validationPassed": draft["validationPassed"],
        }))

    events.append(audit_event("CASH_FORECAST_GENERATED", forecast["summary"], actor="forecasting-tool"))
    for finding in leakage["findings"]:
        events.append(audit_event("LEAKAGE_FINDING_DETECTED", finding, actor="leakage-control-tool"))
    for decision in agent_decisions:
        if decision["chosenAction"] == "DRAFT_REMINDER":
            events.append(audit_event("REMINDER_DECISION_MADE", {
                "studentId": decision["studentId"],
                "action": decision["chosenAction"],
                "reason": decision["reason"],
            }))
    for escalation in escalations:
        events.append(audit_event("CASE_ESCALATED_FOR_REVIEW", escalation))

    events.append(audit_event("FINANCE_RUN_COMPLETED", {
        "studentCount": len(data["students"]),
        "reconciliationCount": len(reconciliation_results),
        "draftCount": len(reminder_drafts),
        "decisionCount": len(agent_decisions),
        "escalationCount": len(escalations),
    }))

    return {
        "status": "COMPLETE",
        "asOf": as_of.isoformat(),
        "dashboard": dashboard,
        "studentPositions": positions,
        "reconciliationResults": reconciliation_results,
        "collectionWorklist": worklist,
        "reminderDrafts": reminder_drafts,
        "forecast": forecast,
        "leakage": leakage,
        "agentDecisions": agent_decisions,
        "escalations": escalations,
        "auditEvents": events,
        "notes": {
            "moneyGuardrail": "All amounts are derived by deterministic Python code using integer paise. The reminder generator is allowed to word messages only.",
            "demoMode": "Local JSON seed data is the default so the assessment demo does not depend on cloud connectivity.",
            "llmMode": "Gemini is optional; when enabled it can word reminders only, and deterministic validation rejects changed amounts or due dates.",
            "agentDecisionPolicy": "The deterministic workflow chooses only DRAFT_REMINDER, ESCALATE_FOR_REVIEW, or SKIP_PAID_OR_PLAN. Drafts remain human-review only.",
            "forecastPolicy": "Cash forecasts are deterministic planning estimates from payment history. They never alter ledger totals, collection targets, or parent communication.",
            "leakagePolicy": "Leakage findings are exception signals that create a review queue. They never reverse fees, refunds, concessions, or payments automatically.",
        },
    }


def maybe_write_firestore(payload: dict[str, Any]) -> None:
    load_dotenv(BASE_DIR / ".env")
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds and not os.path.isabs(creds):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((BASE_DIR / creds).resolve())
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        print("Skipping Firestore write: GCP_PROJECT_ID is missing.")
        return

    from google.cloud import firestore

    # Cloud Run automatically provides Application Default Credentials through
    # its attached service account. Locally, use `gcloud auth application-default login`.
    db = firestore.Client(project=project_id)
    run_ref = db.collection("finance_runs").document()
    run_ref.set({
        "status": payload["status"],
        "asOf": payload["asOf"],
        "dashboard": payload["dashboard"],
        "forecast": payload["forecast"]["summary"],
        "leakageSummary": payload["leakage"]["summary"],
        "createdAt": datetime.now(timezone.utc).isoformat(),
    })
    for name, rows in [
        ("student_positions", payload["studentPositions"]),
        ("reconciliation_results", payload["reconciliationResults"]),
        ("collection_worklist", payload["collectionWorklist"]),
        ("reminder_drafts", payload["reminderDrafts"]),
        ("forecast_students", payload["forecast"]["studentForecasts"]),
        ("leakage_findings", payload["leakage"]["findings"]),
        ("agent_decisions", payload["agentDecisions"]),
        ("escalations", payload["escalations"]),
        ("audit_events", payload["auditEvents"]),
    ]:
        for row in rows:
            run_ref.collection(name).add(row)
    print(f"Wrote Firestore finance run: {run_ref.id}")


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds and not os.path.isabs(creds):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((BASE_DIR / creds).resolve())
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
        "decisionCount": len(payload["agentDecisions"]),
        "escalationCount": len(payload["escalations"]),
        "forecastCashInflow": payload["forecast"]["summary"]["expectedCashInflow"],
        "leakageFindingCount": payload["leakage"]["summary"]["findingCount"],
    }, indent=2))

    if args.firestore:
        maybe_write_firestore(payload)


if __name__ == "__main__":
    main()
