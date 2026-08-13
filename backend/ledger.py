from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def rupees(amount_paise: int) -> str:
    rupee_value = amount_paise / 100
    return f"Rs. {rupee_value:,.0f}"


def ageing_bucket(due_date: date, as_of: date, overdue_paise: int) -> str:
    if overdue_paise <= 0 or due_date >= as_of:
        return "NOT_OVERDUE"
    days = (as_of - due_date).days
    if days <= 30:
        return "0-30"
    if days <= 60:
        return "31-60"
    return "60+"


def calculate_positions(
    *,
    students: list[dict[str, Any]],
    fee_items: list[dict[str, Any]],
    concessions: list[dict[str, Any]],
    waivers: list[dict[str, Any]],
    payments: list[dict[str, Any]],
    payment_plans: list[dict[str, Any]],
    reconciliation_results: list[dict[str, Any]],
    as_of: date,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    students_by_id = {student["studentId"]: student for student in students}
    fees_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    concessions_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    waivers_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    plans_by_student: dict[str, list[dict[str, Any]]] = defaultdict(list)
    matched_payment_ids_by_student: dict[str, list[str]] = defaultdict(list)

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
        if result["confidence"] in {"CONFIDENT", "POSSIBLE"} and result.get("matchedStudentId"):
            matched_payment_ids_by_student[result["matchedStudentId"]].append(result["paymentId"])

    payments_by_id = {payment["paymentId"]: payment for payment in payments}
    positions: list[dict[str, Any]] = []

    dashboard = {
        "asOf": as_of.isoformat(),
        "totalGrossDuePaise": 0,
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

    for student_id, student in students_by_id.items():
        student_fees = fees_by_student[student_id]
        student_concessions = concessions_by_student[student_id]
        student_waivers = waivers_by_student[student_id]
        matched_ids = matched_payment_ids_by_student[student_id]
        matched_payments = [payments_by_id[payment_id] for payment_id in matched_ids]

        gross_due = sum(item["amountPaise"] for item in student_fees)
        concession_total = sum(item["amountPaise"] for item in student_concessions)
        waiver_total = sum(item["amountPaise"] for item in student_waivers)
        paid_total = sum(item["amountPaise"] for item in matched_payments)
        net_due = max(gross_due - concession_total - waiver_total, 0)
        outstanding = max(net_due - paid_total, 0)

        oldest_due_date = min((parse_date(item["dueDate"]) for item in student_fees), default=as_of)
        is_overdue = oldest_due_date < as_of and outstanding > 0
        overdue = outstanding if is_overdue else 0
        bucket = ageing_bucket(oldest_due_date, as_of, overdue)
        days_overdue = max((as_of - oldest_due_date).days, 0) if is_overdue else 0
        has_payment_plan = bool(plans_by_student[student_id])

        position = {
            "studentId": student_id,
            "studentName": student["name"],
            "class": student["class"],
            "guardianName": student["guardianName"],
            "grossDuePaise": gross_due,
            "grossDue": rupees(gross_due),
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
            "ageingBucket": bucket,
            "daysOverdue": days_overdue,
            "hasApprovedPaymentPlan": has_payment_plan,
            "shouldDraftReminder": outstanding > 0 and not has_payment_plan and is_overdue,
            "trace": {
                "feeItemIds": [item["feeItemId"] for item in student_fees],
                "paymentIds": matched_ids,
                "concessionIds": [item["concessionId"] for item in student_concessions],
                "waiverIds": [item["waiverId"] for item in student_waivers],
                "paymentPlanIds": [item["planId"] for item in plans_by_student[student_id]],
            },
        }
        positions.append(position)

        dashboard["totalGrossDuePaise"] += gross_due
        dashboard["totalConcessionPaise"] += concession_total
        dashboard["totalWaiverPaise"] += waiver_total
        dashboard["totalNetDuePaise"] += net_due
        dashboard["totalCollectedPaise"] += paid_total
        dashboard["totalOutstandingPaise"] += outstanding
        dashboard["totalOverduePaise"] += overdue
        dashboard["ageingBuckets"][bucket] += overdue

        class_row = dashboard["byClass"].setdefault(
            student["class"], {"netDuePaise": 0, "collectedPaise": 0, "overduePaise": 0}
        )
        class_row["netDuePaise"] += net_due
        class_row["collectedPaise"] += paid_total
        class_row["overduePaise"] += overdue

        for item in student_fees:
            head_row = dashboard["byFeeHead"].setdefault(
                item["feeHead"], {"grossDuePaise": 0, "count": 0}
            )
            head_row["grossDuePaise"] += item["amountPaise"]
            head_row["count"] += 1
        for payment in matched_payments:
            dashboard["paymentModeBreakdown"][payment["mode"]] = (
                dashboard["paymentModeBreakdown"].get(payment["mode"], 0) + payment["amountPaise"]
            )

    for key in [
        "totalGrossDuePaise",
        "totalConcessionPaise",
        "totalWaiverPaise",
        "totalNetDuePaise",
        "totalCollectedPaise",
        "totalOutstandingPaise",
        "totalOverduePaise",
    ]:
        dashboard[key.replace("Paise", "")] = rupees(dashboard[key])

    for bucket, value in dashboard["ageingBuckets"].items():
        dashboard["ageingBuckets"][bucket] = {"amountPaise": value, "amount": rupees(value)}
    for row in dashboard["byClass"].values():
        row["netDue"] = rupees(row["netDuePaise"])
        row["collected"] = rupees(row["collectedPaise"])
        row["overdue"] = rupees(row["overduePaise"])
    for row in dashboard["byFeeHead"].values():
        row["grossDue"] = rupees(row["grossDuePaise"])
    dashboard["paymentModeBreakdown"] = {
        mode: {"amountPaise": value, "amount": rupees(value)}
        for mode, value in dashboard["paymentModeBreakdown"].items()
    }

    return positions, dashboard


def build_worklist(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bucket_weights = {"60+": 300, "31-60": 200, "0-30": 100, "NOT_OVERDUE": 0}
    rows = []
    for position in positions:
        if position["outstandingPaise"] <= 0:
            continue
        if position["hasApprovedPaymentPlan"]:
            reason = (
                f"{position['studentName']} has {position['outstanding']} outstanding, "
                "but an approved payment plan is already on record."
            )
            should_contact = False
        elif position["overduePaise"] > 0:
            reason = (
                f"{position['studentName']} has {position['outstanding']} outstanding, "
                f"{position['daysOverdue']} days overdue in the {position['ageingBucket']} bucket."
            )
            should_contact = True
        else:
            reason = f"{position['studentName']} has {position['outstanding']} outstanding but it is not overdue yet."
            should_contact = False

        score = (position["overduePaise"] // 1000) + bucket_weights[position["ageingBucket"]]
        rows.append({
            "studentId": position["studentId"],
            "studentName": position["studentName"],
            "class": position["class"],
            "outstandingPaise": position["outstandingPaise"],
            "outstanding": position["outstanding"],
            "ageingBucket": position["ageingBucket"],
            "daysOverdue": position["daysOverdue"],
            "hasApprovedPaymentPlan": position["hasApprovedPaymentPlan"],
            "shouldContact": should_contact,
            "score": score,
            "reason": reason,
        })

    rows.sort(key=lambda row: row["score"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows

