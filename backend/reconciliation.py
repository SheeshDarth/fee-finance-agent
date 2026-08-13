from __future__ import annotations

from typing import Any


def _tokens(value: str) -> set[str]:
    return {part.strip().lower() for part in value.replace(".", " ").split() if len(part.strip()) > 2}


def reconcile_payments(
    students: list[dict[str, Any]],
    fee_items: list[dict[str, Any]],
    payments: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    students_by_id = {student["studentId"]: student for student in students}
    invoice_to_student = {item["feeItemId"]: item["studentId"] for item in fee_items}
    fee_totals_by_student: dict[str, int] = {}
    for item in fee_items:
        fee_totals_by_student[item["studentId"]] = fee_totals_by_student.get(item["studentId"], 0) + item["amountPaise"]

    results = []
    for payment in payments:
        reason = ""
        confidence = "UNMATCHED"
        matched_student_id = None
        requires_review = True

        invoice_ref = payment.get("invoiceRef")
        if invoice_ref and invoice_ref in invoice_to_student:
            matched_student_id = invoice_to_student[invoice_ref]
            confidence = "CONFIDENT"
            reason = f"Invoice reference {invoice_ref} maps directly to student {matched_student_id}."
            requires_review = False
        elif payment.get("studentId") in students_by_id:
            matched_student_id = payment["studentId"]
            confidence = "CONFIDENT"
            reason = f"Payment already carries known student ID {matched_student_id}."
            requires_review = False
        else:
            narration_tokens = _tokens(payment.get("rawNarration", ""))
            candidates = []
            for student in students:
                name_tokens = _tokens(student["name"]) | _tokens(student["guardianName"])
                overlap = narration_tokens & name_tokens
                if overlap:
                    expected = fee_totals_by_student.get(student["studentId"], 0)
                    amount = payment["amountPaise"]
                    amount_plausible = amount <= expected and amount > 0
                    candidates.append((student, overlap, amount_plausible))

            if len(candidates) == 1:
                student, overlap, amount_plausible = candidates[0]
                matched_student_id = student["studentId"]
                confidence = "POSSIBLE" if amount_plausible else "NEEDS_REVIEW"
                reason = (
                    f"Narration overlaps with {student['name']} or guardian tokens "
                    f"{sorted(overlap)}, but no invoice reference was provided."
                )
                requires_review = True
            elif len(candidates) > 1:
                confidence = "NEEDS_REVIEW"
                reason = "Narration matched multiple possible students; human confirmation is required."
            else:
                confidence = "NEEDS_REVIEW"
                reason = "No invoice reference, student ID, or reliable narration match found."

        results.append({
            "paymentId": payment["paymentId"],
            "amountPaise": payment["amountPaise"],
            "mode": payment["mode"],
            "date": payment["date"],
            "rawNarration": payment["rawNarration"],
            "matchedStudentId": matched_student_id,
            "confidence": confidence,
            "requiresHumanReview": requires_review,
            "reason": reason,
        })

    return results

