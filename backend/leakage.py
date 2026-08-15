from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from ledger import parse_date, rupees


def _finding(
    finding_id: str,
    category: str,
    severity: str,
    student_id: str | None,
    amount_paise: int,
    reason: str,
    recommendation: str,
    source_references: list[str],
) -> dict[str, Any]:
    return {
        "findingId": finding_id,
        "category": category,
        "severity": severity,
        "status": "PENDING_HUMAN_REVIEW",
        "studentId": student_id,
        "affectedAmountPaise": amount_paise,
        "affectedAmount": rupees(amount_paise),
        "reason": reason,
        "recommendation": recommendation,
        "sourceReferences": source_references,
    }


def detect_fee_leakage(
    data: dict[str, list[dict[str, Any]]],
    reconciliation_results: list[dict[str, Any]],
    positions: list[dict[str, Any]],
    as_of: date,
) -> dict[str, Any]:
    """Find deterministic integrity exceptions without mutating ledger state."""
    findings: list[dict[str, Any]] = []
    fee_items = data["fee_items"]
    payments = data["payments"]
    payment_by_id = {payment["paymentId"]: payment for payment in payments}
    fee_total_by_student: dict[str, int] = defaultdict(int)
    for item in fee_items:
        fee_total_by_student[item["studentId"]] += int(item["amountPaise"])

    for result in reconciliation_results:
        if result.get("requiresHumanReview"):
            payment_id = result["paymentId"]
            findings.append(_finding(
                f"LEAK-PAYMENT-{payment_id}",
                "UNRECONCILED_PAYMENT",
                "HIGH" if result["confidence"] == "NEEDS_REVIEW" else "MEDIUM",
                result.get("matchedStudentId"),
                int(result["amountPaise"]),
                f"{payment_id} is {result['confidence']} and is excluded from verified collections. {result['reason']}",
                "Confirm or reject the payment allocation before posting it to the ledger.",
                [payment_id],
            ))

    concessions_by_key: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for concession in data["concessions"]:
        amount = int(concession["amountPaise"])
        student_id = concession["studentId"]
        concessions_by_key[(student_id, concession.get("type", "UNKNOWN"), amount)].append(concession)
        if not concession.get("approvedBy"):
            findings.append(_finding(
                f"LEAK-CONCESSION-AUTH-{concession['concessionId']}",
                "UNAPPROVED_CONCESSION",
                "HIGH",
                student_id,
                amount,
                "A concession lacks recorded approving authority.",
                "Hold the concession for authorised approval and supporting evidence.",
                [concession["concessionId"]],
            ))
        if amount > fee_total_by_student.get(student_id, 0):
            findings.append(_finding(
                f"LEAK-CONCESSION-AMOUNT-{concession['concessionId']}",
                "CONCESSION_EXCEEDS_FEE",
                "HIGH",
                student_id,
                amount,
                "A concession exceeds the student's recorded base fee items.",
                "Verify the concession amount and fee basis before applying it.",
                [concession["concessionId"]],
            ))
    for (_, _, amount), duplicates in concessions_by_key.items():
        if len(duplicates) > 1:
            student_id = duplicates[0]["studentId"]
            findings.append(_finding(
                f"LEAK-DUPLICATE-CONCESSION-{student_id}-{duplicates[0].get('type', 'UNKNOWN')}",
                "DUPLICATE_CONCESSION",
                "HIGH",
                student_id,
                amount,
                "More than one concession has the same student, type, and amount.",
                "Confirm whether only one concession should remain applied.",
                [row["concessionId"] for row in duplicates],
            ))

    for plan in data["payment_plans"]:
        scheduled = sum(int(item.get("amountPaise", 0)) for item in plan.get("installments", []))
        total = int(plan.get("totalAmountPaise", 0))
        if scheduled != total:
            findings.append(_finding(
                f"LEAK-PLAN-{plan['planId']}",
                "PAYMENT_PLAN_MISMATCH",
                "HIGH",
                plan.get("studentId"),
                abs(total - scheduled),
                "The approved plan total does not equal its instalment schedule.",
                "Correct the schedule or plan total before relying on plan compliance.",
                [plan["planId"]],
            ))

    for transfer in data.get("transfers", []):
        if transfer.get("status") != "COMPLETED":
            continue
        effective_date = parse_date(transfer["effectiveDate"])
        billed_after_transfer = [
            item for item in fee_items
            if item["studentId"] == transfer["studentId"] and parse_date(item["dueDate"]) > effective_date
        ]
        if billed_after_transfer:
            amount = sum(int(item["amountPaise"]) for item in billed_after_transfer)
            findings.append(_finding(
                f"LEAK-TRANSFER-{transfer['transferId']}",
                "BILLING_AFTER_TRANSFER",
                "HIGH",
                transfer["studentId"],
                amount,
                "Fee items remain due after a completed student transfer.",
                "Verify enrolment status and reverse or hold post-transfer billing before collection contact.",
                [transfer["transferId"], *[item["feeItemId"] for item in billed_after_transfer]],
            ))

    for refund in data.get("refunds", []):
        amount = int(refund["amountPaise"])
        payment = payment_by_id.get(refund.get("paymentId"))
        if not refund.get("approvedBy"):
            findings.append(_finding(
                f"LEAK-REFUND-AUTH-{refund['refundId']}",
                "UNAPPROVED_REFUND",
                "HIGH",
                refund.get("studentId"),
                amount,
                "A refund record has no approving authority.",
                "Hold the refund until an authorised reviewer verifies the reason and payment evidence.",
                [refund["refundId"], *([refund["paymentId"]] if refund.get("paymentId") else [])],
            ))
        if payment and amount > int(payment["amountPaise"]):
            findings.append(_finding(
                f"LEAK-REFUND-AMOUNT-{refund['refundId']}",
                "REFUND_EXCEEDS_RECEIPT",
                "HIGH",
                refund.get("studentId"),
                amount,
                "The refund amount exceeds the referenced receipt amount.",
                "Investigate the refund before it is paid or posted.",
                [refund["refundId"], payment["paymentId"]],
            ))

    for adjustment in data.get("manual_adjustments", []):
        if not adjustment.get("approvedBy"):
            amount = abs(int(adjustment.get("amountPaise", 0)))
            findings.append(_finding(
                f"LEAK-ADJUSTMENT-{adjustment['adjustmentId']}",
                "UNAPPROVED_MANUAL_ADJUSTMENT",
                "HIGH",
                adjustment.get("studentId"),
                amount,
                "A manual adjustment lacks recorded approving authority.",
                "Do not apply the adjustment until an authorised reviewer supplies evidence.",
                [adjustment["adjustmentId"]],
            ))

    duplicate_groups: dict[tuple[str | None, str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for payment in payments:
        duplicate_groups[(payment.get("studentId"), payment["date"], int(payment["amountPaise"]), payment["mode"], payment["rawNarration"])].append(payment)
    for duplicates in duplicate_groups.values():
        if len(duplicates) > 1:
            amount = int(duplicates[0]["amountPaise"])
            findings.append(_finding(
                f"LEAK-DUPLICATE-RECEIPT-{duplicates[0]['paymentId']}",
                "DUPLICATE_RECEIPT",
                "HIGH",
                duplicates[0].get("studentId"),
                amount,
                "Payments share student, date, amount, mode, and narration.",
                "Confirm whether one record is duplicated before posting or refunding it.",
                [payment["paymentId"] for payment in duplicates],
            ))

    findings.sort(key=lambda row: ({"HIGH": 0, "MEDIUM": 1, "LOW": 2}[row["severity"]], row["findingId"]))
    risk_keys = set()
    amount_at_risk = 0
    for finding in findings:
        key = tuple(sorted(finding["sourceReferences"]))
        if key not in risk_keys:
            risk_keys.add(key)
            amount_at_risk += finding["affectedAmountPaise"]
    summary = {
        "asOf": as_of.isoformat(),
        "findingCount": len(findings),
        "highSeverityCount": sum(1 for row in findings if row["severity"] == "HIGH"),
        "mediumSeverityCount": sum(1 for row in findings if row["severity"] == "MEDIUM"),
        "amountAtRiskPaise": amount_at_risk,
        "amountAtRisk": rupees(amount_at_risk),
        "status": "REVIEW_REQUIRED" if findings else "NO_EXCEPTION_FOUND",
        "limitation": "Control findings are exception signals, not proof of loss. Overlapping source records are de-duplicated only when the source set is identical.",
    }
    return {"summary": summary, "findings": findings}
