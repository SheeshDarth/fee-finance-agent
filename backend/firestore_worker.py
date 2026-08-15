from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_runner import build_finance_run
from google.cloud.firestore_v1.base_query import FieldFilter
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        return False


def _firestore_client():
    from google.cloud import firestore

    return firestore.Client(project=os.getenv("GCP_PROJECT_ID"))


def publish_run(db: Any, run_ref: Any, payload: dict[str, Any]) -> None:
    review_required = bool(
        any(row.get("requiresHumanReview") for row in payload["reconciliationResults"])
        or payload["reminderDrafts"]
    )
    run_ref.set({
        "status": "AWAITING_REVIEW" if review_required else "COMPLETE",
        "asOf": payload["asOf"],
        "dashboard": payload["dashboard"],
        "forecast": payload["forecast"]["summary"],
        "leakageSummary": payload["leakage"]["summary"],
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }, merge=True)
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


def process_run(db: Any, run_snapshot: Any) -> None:
    run_ref = run_snapshot.reference
    run_ref.set({"status": "RUNNING", "startedAt": datetime.now(timezone.utc).isoformat()}, merge=True)
    try:
        data = run_snapshot.to_dict()
        as_of = datetime.strptime(data.get("asOf", "2026-08-13"), "%Y-%m-%d").date()
        override_data = data.get("customData")
        payload = build_finance_run(as_of, use_llm=os.getenv("ENABLE_LLM", "false").lower() == "true", override_data=override_data)
        publish_run(db, run_ref, payload)
    except Exception as error:
        run_ref.set({"status": "FAILED", "error": str(error), "updatedAt": datetime.now(timezone.utc).isoformat()}, merge=True)


def process_review_actions_once(db: Any) -> None:
    for run_snapshot in db.collection("finance_runs").stream():
        actions = run_snapshot.reference.collection("review_actions").where(filter=FieldFilter("status", "==", "PENDING")).stream()
        for action in actions:
            action.reference.set({
                "status": "APPLIED",
                "processedAt": datetime.now(timezone.utc).isoformat(),
                "processor": "firestore-worker",
            }, merge=True)
            run_snapshot.reference.collection("audit_events").add({
                "eventType": "REVIEW_ACTION_APPLIED",
                "actor": "firestore-worker",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": action.to_dict(),
            })


def run_once(db: Any) -> None:
    for snapshot in db.collection("finance_runs").where(filter=FieldFilter("status", "==", "PENDING")).stream():
        process_run(db, snapshot)
    process_review_actions_once(db)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    load_dotenv(base_dir / ".env")
    creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds and not os.path.isabs(creds):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((base_dir / creds).resolve())
    parser = argparse.ArgumentParser(description="Process pending FeeOps Firestore runs.")
    parser.add_argument("--once", action="store_true", help="Process pending runs once and exit.")
    args = parser.parse_args()
    db = _firestore_client()
    if args.once:
        run_once(db)
        return
    while True:
        run_once(db)
        time.sleep(int(os.getenv("WORKER_POLL_SECONDS", "10")))


if __name__ == "__main__":
    main()
