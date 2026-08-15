from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from ledger import parse_date, rupees


def _clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(value, maximum))


def _history_totals(records: list[dict[str, Any]], student_id: str | None = None) -> tuple[int, int, int]:
    scoped = [record for record in records if student_id is None or record.get("studentId") == student_id]
    expected = sum(max(int(record.get("expectedPaise", 0)), 0) for record in scoped)
    paid = sum(min(max(int(record.get("amountPaise", 0)), 0), max(int(record.get("expectedPaise", 0)), 0)) for record in scoped)
    return expected, paid, len(scoped)


def _timing_adjustment_bps(history: dict[str, Any]) -> int:
    if history.get("missedPaymentCount", 0):
        return 3_500
    if history.get("partialPaymentCount", 0):
        return 6_500
    if history.get("averageDaysLate", 0) > 14:
        return 7_500
    if history.get("averageDaysLate", 0) > 0:
        return 8_500
    return 10_000


def _delay_risk(history: dict[str, Any], recovery_bps: int) -> str:
    if history.get("missedPaymentCount", 0) or recovery_bps < 5_000:
        return "HIGH"
    if history.get("partialPaymentCount", 0) or history.get("latePaymentCount", 0):
        return "MEDIUM"
    return "LOW"


def build_cash_forecast(
    positions: list[dict[str, Any]],
    payment_history: list[dict[str, Any]],
    dashboard: dict[str, Any],
    as_of: date,
    horizon_days: int = 30,
) -> dict[str, Any]:
    """Project expected collections from deterministic history, not LLM judgement.

    The output is a planning estimate only. A blended global prior prevents a
    single historical payment from being treated as a precise probability.
    """
    horizon_end = as_of + timedelta(days=horizon_days)
    global_expected, global_paid, total_records = _history_totals(payment_history)
    global_recovery_bps = (global_paid * 10_000 // global_expected) if global_expected else 7_000
    prior_paise = 2_000_000
    student_forecasts: list[dict[str, Any]] = []

    for position in positions:
        forecastable_outstanding = sum(
            int(item["outstandingPaise"])
            for item in position["feeItems"]
            if parse_date(item["dueDate"]) <= horizon_end
        )
        history_expected, history_paid, record_count = _history_totals(payment_history, position["studentId"])
        recovery_bps = (
            (history_paid * 10_000 + global_recovery_bps * prior_paise)
            // (history_expected + prior_paise)
            if history_expected + prior_paise
            else global_recovery_bps
        )
        recovery_bps = _clamp(recovery_bps, 0, 10_000)
        timing_bps = _timing_adjustment_bps(position["paymentHistory"])
        expected_collection = forecastable_outstanding * recovery_bps * timing_bps // 100_000_000
        delay_risk = _delay_risk(position["paymentHistory"], recovery_bps)
        reason = (
            f"{record_count} history record(s); blended recovery rate {recovery_bps / 100:.0f}% "
            f"and timing adjustment {timing_bps / 100:.0f}% based on payment behaviour."
        )
        student_forecasts.append({
            "studentId": position["studentId"],
            "studentName": position["studentName"],
            "class": position["class"],
            "forecastableOutstandingPaise": forecastable_outstanding,
            "forecastableOutstanding": rupees(forecastable_outstanding),
            "historicalRecordCount": record_count,
            "recoveryRateBps": recovery_bps,
            "recoveryRatePercent": round(recovery_bps / 100, 1),
            "timingAdjustmentBps": timing_bps,
            "expectedCollectionPaise": expected_collection,
            "expectedCollection": rupees(expected_collection),
            "delayRisk": delay_risk,
            "reason": reason,
        })

    expected_collection = sum(row["expectedCollectionPaise"] for row in student_forecasts)
    assessed_due = int(dashboard["totalNetDuePaise"])
    current_collected = int(dashboard["totalCollectedPaise"])
    projected_outstanding = max(int(dashboard["totalOutstandingPaise"]) - expected_collection, 0)
    projected_collection_rate_bps = (current_collected + expected_collection) * 10_000 // assessed_due if assessed_due else 0
    confidence = "LOW" if total_records < 8 else "MEDIUM" if total_records < 24 else "HIGH"
    likely_to_delay = sorted(
        [row for row in student_forecasts if row["delayRisk"] in {"HIGH", "MEDIUM"} and row["forecastableOutstandingPaise"] > 0],
        key=lambda row: (row["delayRisk"] == "HIGH", -row["expectedCollectionPaise"]),
        reverse=True,
    )

    return {
        "summary": {
            "model": "EMPIRICAL_HISTORY_BLEND_V1",
            "asOf": as_of.isoformat(),
            "horizonDays": horizon_days,
            "horizonEnd": horizon_end.isoformat(),
            "historicalRecordCount": total_records,
            "forecastConfidence": confidence,
            "expectedCashInflowPaise": expected_collection,
            "expectedCashInflow": rupees(expected_collection),
            "expectedOutstandingPaise": projected_outstanding,
            "expectedOutstanding": rupees(projected_outstanding),
            "projectedCollectionRateBps": projected_collection_rate_bps,
            "projectedCollectionRatePercent": round(projected_collection_rate_bps / 100, 1),
            "likelyDelayStudentIds": [row["studentId"] for row in likely_to_delay],
            "limitation": "Planning estimate only. The demo has sparse payment history; it is not a statistical guarantee or an annual-budget forecast.",
        },
        "studentForecasts": student_forecasts,
    }
