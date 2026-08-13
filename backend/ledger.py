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
        if (
            result["confidence"] == "CONFIDENT"
            and not result.get("requiresHumanReview")
            and result.get("matchedStudentId")
        ):
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
        student_fees = sorted(
            fees_by_student[student_id],
            key=lambda item: (parse_date(item["dueDate"]), item["feeItemId"]),
        )
        student_concessions = concessions_by_student[student_id]
        student_waivers = waivers_by_student[student_id]
        matched_ids = matched_payment_ids_by_student[student_id]
        matched_payments = [payments_by_id[payment_id] for payment_id in matched_ids]
        pending_review_ids = [
            result["paymentId"]
            for result in reconciliation_results
            if result.get("matchedStudentId") == student_id
            and result.get("requiresHumanReview")
        ]

        gross_due = sum(item["amountPaise"] + item.get("lateFeePaise", 0) for item in student_fees)
        concession_total = sum(item["amountPaise"] for item in student_concessions)
        waiver_total = sum(item["amountPaise"] for item in student_waivers)
        has_payment_plan = bool(plans_by_student[student_id])

        # Allocate student-level adjustments and approved payments FIFO by due date.
        # This keeps ageing and fee-head totals tied to individual billing items.
        remaining_adjustment = concession_total + waiver_total
        remaining_payment = sum(item["amountPaise"] for item in matched_payments)
        item_positions = []
        for item in student_fees:
            line_gross = item["amountPaise"] + item.get("lateFeePaise", 0)
            item_adjustment = min(line_gross, remaining_adjustment)
            remaining_adjustment -= item_adjustment
            line_net = line_gross - item_adjustment
            item_payment = min(line_net, remaining_payment)
            remaining_payment -= item_payment
            item_outstanding = line_net - item_payment
            item_due_date = parse_date(item["dueDate"])
            item_overdue = item_outstanding if item_due_date < as_of else 0
            item_bucket = ageing_bucket(item_due_date, as_of, item_overdue)
            item_positions.append({
                "feeItemId": item["feeItemId"],
                "feeHead": item["feeHead"],
                "term": item.get("term"),
                "dueDate": item["dueDate"],
                "grossDuePaise": line_gross,
                "adjustmentPaise": item_adjustment,
                "netDuePaise": line_net,
                "collectedPaise": item_payment,
                "outstandingPaise": item_outstanding,
                "overduePaise": item_overdue,
                "ageingBucket": item_bucket,
                "daysOverdue": max((as_of - item_due_date).days, 0) if item_overdue else 0,
            })

        paid_total = sum(item["collectedPaise"] for item in item_positions)
        net_due = sum(item["netDuePaise"] for item in item_positions)
        outstanding = sum(item["outstandingPaise"] for item in item_positions)
        overdue = sum(item["overduePaise"] for item in item_positions)
        overdue_items = [item for item in item_positions if item["overduePaise"] > 0]
        oldest_overdue_days = max((item["daysOverdue"] for item in overdue_items), default=0)
        bucket = max(
            (item["ageingBucket"] for item in overdue_items),
            key=lambda value: {"0-30": 1, "31-60": 2, "60+": 3}.get(value, 0),
            default="NOT_OVERDUE",
        )
        is_overdue = overdue > 0

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
            "daysOverdue": oldest_overdue_days,
            "hasApprovedPaymentPlan": has_payment_plan,
            "shouldDraftReminder": outstanding > 0 and not has_payment_plan and is_overdue,
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
        dashboard["totalConcessionPaise"] += concession_total
        dashboard["totalWaiverPaise"] += waiver_total
        dashboard["totalNetDuePaise"] += net_due
        dashboard["totalCollectedPaise"] += paid_total
        dashboard["totalOutstandingPaise"] += outstanding
        dashboard["totalOverduePaise"] += overdue
        for item in item_positions:
            dashboard["ageingBuckets"][item["ageingBucket"]] += item["outstandingPaise"] if item["ageingBucket"] == "NOT_OVERDUE" else item["overduePaise"]

        class_row = dashboard["byClass"].setdefault(
            student["class"], {"netDuePaise": 0, "collectedPaise": 0, "overduePaise": 0}
        )
        class_row["netDuePaise"] += net_due
        class_row["collectedPaise"] += paid_total
        class_row["overduePaise"] += overdue

        for item in item_positions:
            head_row = dashboard["byFeeHead"].setdefault(
                item["feeHead"], {
                    "grossDuePaise": 0,
                    "netDuePaise": 0,
                    "collectedPaise": 0,
                    "outstandingPaise": 0,
                    "overduePaise": 0,
                    "count": 0,
                }
            )
            head_row["grossDuePaise"] += item["grossDuePaise"]
            head_row["netDuePaise"] += item["netDuePaise"]
            head_row["collectedPaise"] += item["collectedPaise"]
            head_row["outstandingPaise"] += item["outstandingPaise"]
            head_row["overduePaise"] += item["overduePaise"]
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
        row["netDue"] = rupees(row["netDuePaise"])
        row["collected"] = rupees(row["collectedPaise"])
        row["outstanding"] = rupees(row["outstandingPaise"])
        row["overdue"] = rupees(row["overduePaise"])
    pending_review_total = sum(
        result["amountPaise"]
        for result in reconciliation_results
        if result.get("requiresHumanReview")
    )
    dashboard["pendingReviewPaise"] = pending_review_total
    dashboard["pendingReview"] = rupees(pending_review_total)
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
