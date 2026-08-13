from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def rupees(amount_paise: int) -> str:
    whole_rupees, paise = divmod(amount_paise, 100)
    suffix = f".{paise:02d}" if paise else ""
    return f"Rs. {whole_rupees:,}{suffix}"


def ageing_bucket(due_date: date, as_of: date, overdue_paise: int) -> str:
    if overdue_paise <= 0 or due_date >= as_of:
        return "NOT_OVERDUE"
    days = (as_of - due_date).days
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    return "60+"


def calculate_late_fee(item: dict[str, Any], as_of: date) -> int:
    """Calculate a fee-item late charge from policy metadata only."""
    due_date = parse_date(item["dueDate"])
    policy = item.get("lateFeePolicy") or {}
    overdue_days = max((as_of - due_date).days, 0)
    billable_days = max(overdue_days - int(policy.get("graceDays", 0)), 0)
    if billable_days <= 0:
        return 0
    if policy.get("type") == "fixed_after_grace":
        return int(policy.get("amountPaise", 0))
    if policy.get("type") == "daily":
        calculated = billable_days * int(policy.get("dailyAmountPaise", 0))
        return min(calculated, int(policy.get("capPaise", calculated)))
    return 0


def _history_summary(records: list[dict[str, Any]], student_id: str, as_of: date) -> dict[str, Any]:
    student_records = [record for record in records if record.get("studentId") == student_id]
    late_days = [max(int(record.get("daysLate", 0)), 0) for record in student_records]
    late_count = sum(1 for days in late_days if days > 0)
    partial_count = sum(1 for record in student_records if record.get("paymentType") == "PARTIAL")
    missed_count = sum(1 for record in student_records if record.get("paymentType") == "MISSED")
    average_days_late = round(sum(late_days) / len(late_days), 1) if late_days else 0
    dated_records = [record for record in student_records if record.get("paymentDate")]
    last_payment = max(
        (parse_date(record["paymentDate"]) for record in dated_records),
        default=None,
    )
    return {
        "recordCount": len(student_records),
        "latePaymentCount": late_count,
        "partialPaymentCount": partial_count,
        "missedPaymentCount": missed_count,
        "averageDaysLate": average_days_late,
        "lastPaymentDate": last_payment.isoformat() if last_payment else None,
        "historyRisk": "HIGH" if missed_count or partial_count > 1 else "MEDIUM" if late_count else "LOW",
        "asOf": as_of.isoformat(),
    }


def _plan_summary(
    plans: list[dict[str, Any]],
    payment_by_id: dict[str, dict[str, Any]],
    reconciliation_by_payment: dict[str, dict[str, Any]],
    as_of: date,
) -> dict[str, Any] | None:
    if not plans:
        return None
    plan = sorted(plans, key=lambda row: row.get("approvedAt", ""), reverse=True)[0]
    installments = []
    for installment in plan.get("installments", []):
        verified_paid = 0
        pending_amount = 0
        for payment_id in installment.get("paymentIds", []):
            payment = payment_by_id.get(payment_id)
            result = reconciliation_by_payment.get(payment_id)
            if not payment or not result:
                continue
            if result.get("confidence") == "CONFIDENT" and not result.get("requiresHumanReview"):
                verified_paid += int(payment["amountPaise"])
            else:
                pending_amount += int(payment["amountPaise"])
        scheduled = int(installment.get("amountPaise", 0))
        remaining = max(scheduled - verified_paid, 0)
        due_date = parse_date(installment["dueDate"])
        installments.append({
            "installmentId": installment["installmentId"],
            "dueDate": installment["dueDate"],
            "amountPaise": scheduled,
            "amount": rupees(scheduled),
            "paidPaise": verified_paid,
            "paid": rupees(verified_paid),
            "pendingReviewPaise": pending_amount,
            "pendingReview": rupees(pending_amount),
            "remainingPaise": remaining,
            "remaining": rupees(remaining),
            "status": "COMPLETE" if remaining == 0 else "OVERDUE" if due_date < as_of else "PENDING",
        })
    overdue = [row for row in installments if row["status"] == "OVERDUE"]
    next_due = next((row["dueDate"] for row in installments if row["remainingPaise"] > 0), None)
    return {
        "planId": plan["planId"],
        "status": plan["status"],
        "approvedBy": plan.get("approvedBy"),
        "approvedAt": plan.get("approvedAt"),
        "totalAmountPaise": int(plan.get("totalAmountPaise", 0)),
        "totalAmount": rupees(int(plan.get("totalAmountPaise", 0))),
        "installments": installments,
        "verifiedPaidPaise": sum(row["paidPaise"] for row in installments),
        "verifiedPaid": rupees(sum(row["paidPaise"] for row in installments)),
        "remainingPaise": sum(row["remainingPaise"] for row in installments),
        "remaining": rupees(sum(row["remainingPaise"] for row in installments)),
        "overduePaise": sum(row["remainingPaise"] for row in overdue),
        "overdue": rupees(sum(row["remainingPaise"] for row in overdue)),
        "nextDueDate": next_due,
        "compliance": "OVERDUE" if overdue else "COMPLETE" if installments and all(row["remainingPaise"] == 0 for row in installments) else "ON_TRACK",
    }


def calculate_positions(
    *,
    students: list[dict[str, Any]],
    fee_items: list[dict[str, Any]],
    concessions: list[dict[str, Any]],
    waivers: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    payment_plans: list[dict[str, Any]],
    payment_history: list[dict[str, Any]] | None = None,
    reconciliation_results: list[dict[str, Any]],
    as_of: date,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    students_by_id = {student["studentId"]: student for student in students}
    fees_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    concessions_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    waivers_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    plans_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    matched_payment_ids_by_student: dict[str, list[str]] = defaultdict(list)
    reconciliation_by_payment = {result["paymentId"]: result for result in reconciliation_results}
    payments_by_id = {payment["paymentId"]: payment for payment in payments}

    for item in fee_items:
        fees_by_student[item["studentId"]].append(item)
    for concession in concessions:
        concessions_by_student[concession["studentId"]].append(concession)
    for waiver in waivers:
        waivers_by_student[waiver["studentId"]].append(waiver)
    for plan in payment_plans:
        if plan.get("status") == "APPROVED":
            plans_by_student[plan["studentId"]].append(plan)
    for result in reconciliation_results:
        if result["confidence"] == "CONFIDENT" and not result.get("requiresHumanReview") and result.get("matchedStudentId"):
            matched_payment_ids_by_student[result["matchedStudentId"]].append(result["paymentId"])

    dashboard = {
        "asOf": as_of.isoformat(),
        "totalGrossDuePaise": 0,
        "totalLateFeePaise": 0,
        "totalConcessionPaise": 0,
        "totalWaiverPaise": 0,
        "totalNetDuePaise": 0,
        "totalCollectedPaise": 0,
        "totalOutstandingPaise": 0,
        "totalOverduePaise": 0,
        "ageingBuckets": {"0-30": 0, "31-60": 0, "60+": 0, "NOT_OVERDUE": 0},
        "byClass": {},
        "byFeeHead": {},
        "paymentModeBreakdown": {},
    }
    positions: list[dict[str, Any]] = []
    history_records = payment_history or []

    for student_id, student in students_by_id.items():
        student_fees = sorted(fees_by_student[student_id], key=lambda item: (parse_date(item["dueDate"]), item["feeItemId"]))
        student_concessions = concessions_by_student[student_id]
        student_waivers = waivers_by_student[student_id]
        matched_ids = matched_payment_ids_by_student[student_id]
        matched_payments = [payments_by_id[payment_id] for payment_id in matched_ids]
        pending_review_ids = [
            result["paymentId"] for result in reconciliation_results
            if result.get("matchedStudentId") == student_id and result.get("requiresHumanReview")
        ]
        enriched_fees = [{**item, "lateFeePaise": calculate_late_fee(item, as_of)} for item in student_fees]
        gross_due = sum(item["amountPaise"] + item["lateFeePaise"] for item in enriched_fees)
        late_fee_total = sum(item["lateFeePaise"] for item in enriched_fees)
        concession_total = sum(item["amountPaise"] for item in student_concessions)
        waiver_total = sum(item["amountPaise"] for item in student_waivers)
        remaining_adjustment = concession_total + waiver_total
        remaining_payment = sum(item["amountPaise"] for item in matched_payments)
        item_positions = []
        for item in enriched_fees:
            line_gross = item["amountPaise"] + item["lateFeePaise"]
            item_adjustment = min(line_gross, remaining_adjustment)
            remaining_adjustment -= item_adjustment
            line_net = line_gross - item_adjustment
            item_payment = min(line_net, remaining_payment)
            remaining_payment -= item_payment
            item_outstanding = line_net - item_payment
            item_due_date = parse_date(item["dueDate"])
            item_overdue = item_outstanding if item_due_date < as_of else 0
            item_positions.append({
                "feeItemId": item["feeItemId"],
                "feeHead": item["feeHead"],
                "term": item.get("term"),
                "instalmentId": item.get("instalmentId"),
                "instalmentNumber": item.get("instalmentNumber"),
                "dueDate": item["dueDate"],
                "baseAmountPaise": item["amountPaise"],
                "lateFeePaise": item["lateFeePaise"],
                "lateFee": rupees(item["lateFeePaise"]),
                "grossDuePaise": line_gross,
                "adjustmentPaise": item_adjustment,
                "netDuePaise": line_net,
                "collectedPaise": item_payment,
                "outstandingPaise": item_outstanding,
                "overduePaise": item_overdue,
                "ageingBucket": ageing_bucket(item_due_date, as_of, item_overdue),
                "daysOverdue": max((as_of - item_due_date).days, 0) if item_overdue else 0,
            })

        paid_total = sum(item["collectedPaise"] for item in item_positions)
        net_due = sum(item["netDuePaise"] for item in item_positions)
        outstanding = sum(item["outstandingPaise"] for item in item_positions)
        overdue = sum(item["overduePaise"] for item in item_positions)
        overdue_items = [item for item in item_positions if item["overduePaise"] > 0]
        oldest_overdue_days = max((item["daysOverdue"] for item in overdue_items), default=0)
        bucket = max((item["ageingBucket"] for item in overdue_items), key=lambda value: {"0-30": 1, "31-60": 2, "60+": 3}.get(value, 0), default="NOT_OVERDUE")
        reminder_due_date = min((item["dueDate"] for item in overdue_items), default=None)
        history = _history_summary(history_records, student_id, as_of)
        plan = _plan_summary(plans_by_student[student_id], payments_by_id, reconciliation_by_payment, as_of)
        position = {
            "studentId": student_id,
            "studentName": student["name"],
            "class": student["class"],
            "guardianName": student["guardianName"],
            "grossDuePaise": gross_due,
            "grossDue": rupees(gross_due),
            "lateFeePaise": late_fee_total,
            "lateFee": rupees(late_fee_total),
            "concessionPaise": concession_total,
            "concession": rupees(concession_total),
            "waiverPaise": waiver_total,
            "waiver": rupees(waiver_total),
            "netDuePaise": net_due,
            "netDue": rupees(net_due),
            "paidPaise": paid_total,
            "paid": rupees(paid_total),
            "outstandingPaise": outstanding,
            "outstanding": rupees(outstanding),
            "overduePaise": overdue,
            "overdue": rupees(overdue),
            "overdueOutstandingPaise": overdue,
            "overdueOutstanding": rupees(overdue),
            "ageingBucket": bucket,
            "daysOverdue": oldest_overdue_days,
            "reminderDueDate": reminder_due_date,
            "reminderAmountPaise": overdue,
            "reminderAmount": rupees(overdue),
            "hasApprovedPaymentPlan": plan is not None,
            "paymentPlan": plan,
            "planCompliance": plan["compliance"] if plan else "NO_PLAN",
            "paymentHistory": history,
            "shouldDraftReminder": overdue > 0 and plan is None,
            "feeItems": item_positions,
            "trace": {
                "feeItemIds": [item["feeItemId"] for item in student_fees],
                "paymentIds": matched_ids,
                "pendingReviewPaymentIds": pending_review_ids,
                "concessionIds": [item["concessionId"] for item in student_concessions],
                "waiverIds": [item["waiverId"] for item in student_waivers],
                "paymentPlanIds": [item["planId"] for item in plans_by_student[student_id]],
            },
        }
        positions.append(position)
        dashboard["totalGrossDuePaise"] += gross_due
        dashboard["totalLateFeePaise"] += late_fee_total
        dashboard["totalConcessionPaise"] += concession_total
        dashboard["totalWaiverPaise"] += waiver_total
        dashboard["totalNetDuePaise"] += net_due
        dashboard["totalCollectedPaise"] += paid_total
        dashboard["totalOutstandingPaise"] += outstanding
        dashboard["totalOverduePaise"] += overdue
        for item in item_positions:
            dashboard["ageingBuckets"][item["ageingBucket"]] += item["outstandingPaise"] if item["ageingBucket"] == "NOT_OVERDUE" else item["overduePaise"]
        class_row = dashboard["byClass"].setdefault(student["class"], {"netDuePaise": 0, "collectedPaise": 0, "overduePaise": 0})
        class_row["netDuePaise"] += net_due
        class_row["collectedPaise"] += paid_total
        class_row["overduePaise"] += overdue
        for item in item_positions:
            head_row = dashboard["byFeeHead"].setdefault(item["feeHead"], {"grossDuePaise": 0, "netDuePaise": 0, "collectedPaise": 0, "outstandingPaise": 0, "overduePaise": 0, "lateFeePaise": 0, "count": 0})
            head_row["grossDuePaise"] += item["grossDuePaise"]
            head_row["netDuePaise"] += item["netDuePaise"]
            head_row["collectedPaise"] += item["collectedPaise"]
            head_row["outstandingPaise"] += item["outstandingPaise"]
            head_row["overduePaise"] += item["overduePaise"]
            head_row["lateFeePaise"] += item["lateFeePaise"]
            head_row["count"] += 1
        for payment in matched_payments:
            dashboard["paymentModeBreakdown"][payment["mode"]] = dashboard["paymentModeBreakdown"].get(payment["mode"], 0) + payment["amountPaise"]

    for key in ["totalGrossDuePaise", "totalLateFeePaise", "totalConcessionPaise", "totalWaiverPaise", "totalNetDuePaise", "totalCollectedPaise", "totalOutstandingPaise", "totalOverduePaise"]:
        dashboard[key.replace("Paise", "")] = rupees(dashboard[key])
    for bucket, value in dashboard["ageingBuckets"].items():
        dashboard["ageingBuckets"][bucket] = {"amountPaise": value, "amount": rupees(value)}
    for row in dashboard["byClass"].values():
        row["netDue"] = rupees(row["netDuePaise"])
        row["collected"] = rupees(row["collectedPaise"])
        row["overdue"] = rupees(row["overduePaise"])
    for row in dashboard["byFeeHead"].values():
        for key in ["grossDuePaise", "netDuePaise", "collectedPaise", "outstandingPaise", "overduePaise", "lateFeePaise"]:
            row[key.replace("Paise", "")] = rupees(row[key])
    pending_review_total = sum(result["amountPaise"] for result in reconciliation_results if result.get("requiresHumanReview"))
    dashboard["pendingReviewPaise"] = pending_review_total
    dashboard["pendingReview"] = rupees(pending_review_total)
    dashboard["paymentModeBreakdown"] = {mode: {"amountPaise": value, "amount": rupees(value)} for mode, value in dashboard["paymentModeBreakdown"].items()}
    return positions, dashboard


def build_worklist(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket_weights = {"60+": 300, "31-60": 200, "0-30": 100, "NOT_OVERDUE": 0}
    rows = []
    for position in positions:
        if position["outstandingPaise"] <= 0:
            continue
        history = position["paymentHistory"]
        amount_component = position["overduePaise"] // 1000
        age_component = bucket_weights[position["ageingBucket"]]
        late_component = history["latePaymentCount"] * 25
        partial_component = history["partialPaymentCount"] * 50
        missed_component = history["missedPaymentCount"] * 75
        delay_component = min(int(history["averageDaysLate"] * 2), 100)
        score = amount_component + age_component + late_component + partial_component + missed_component + delay_component
        if position["hasApprovedPaymentPlan"]:
            reason = f"{position['studentName']} has {position['outstanding']} outstanding, but an approved plan is on file ({position['planCompliance'].lower()}); history shows {history['latePaymentCount']} late, {history['partialPaymentCount']} partial, and {history['missedPaymentCount']} missed payment(s)."
            should_contact = False
        elif position["overduePaise"] > 0:
            reason = f"{position['studentName']} has {position['overdueOutstanding']} overdue in {position['ageingBucket']}; history shows {history['latePaymentCount']} late, {history['partialPaymentCount']} partial, and {history['missedPaymentCount']} missed payment(s)."
            should_contact = True
        else:
            reason = f"{position['studentName']} has {position['outstanding']} outstanding but it is not overdue yet; payment history risk is {history['historyRisk'].lower()}."
            should_contact = False
        rows.append({
            "studentId": position["studentId"],
            "studentName": position["studentName"],
            "class": position["class"],
            "outstandingPaise": position["outstandingPaise"],
            "outstanding": position["outstanding"],
            "overduePaise": position["overduePaise"],
            "overdue": position["overdue"],
            "ageingBucket": position["ageingBucket"],
            "daysOverdue": position["daysOverdue"],
            "hasApprovedPaymentPlan": position["hasApprovedPaymentPlan"],
            "planCompliance": position["planCompliance"],
            "paymentHistory": history,
            "scoreBreakdown": {"overdueAmount": amount_component, "ageing": age_component, "lateHistory": late_component, "partialHistory": partial_component, "missedHistory": missed_component, "averageDelay": delay_component},
            "shouldContact": should_contact,
            "score": score,
            "reason": reason,
        })
    rows.sort(key=lambda row: row["score"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows
