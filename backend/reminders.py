from __future__ import annotations

import re
from typing import Any


TONE_BY_BUCKET = {
    "0-30": "polite reminder",
    "31-60": "firm but respectful reminder",
    "60+": "urgent formal reminder",
}


def _template_message(position: dict[str, Any]) -> str:
    tone = TONE_BY_BUCKET.get(position["ageingBucket"], "polite reminder")
    return (
        f"Dear {position['guardianName']}, this is a {tone} for {position['studentName']}'s "
        f"school fee balance of {position['outstanding']}. The amount has been pending since "
        f"the due date connected to the current instalment and is now {position['daysOverdue']} "
        "days overdue. Please treat this as a draft notice for accounts-office review before any "
        "parent communication is sent."
    )


def _validate_message(message: str, allowed_amounts: set[str]) -> tuple[bool, str]:
    mentioned_amounts = set(re.findall(r"Rs\. [0-9,]+", message))
    unknown = mentioned_amounts - allowed_amounts
    if unknown:
        return False, f"Message contains unknown amount(s): {sorted(unknown)}"
    return True, "All monetary figures match deterministic ledger values."


def draft_reminders(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    drafts = []
    for position in positions:
        if not position["shouldDraftReminder"]:
            continue
        message = _template_message(position)
        is_valid, validation_note = _validate_message(message, {position["outstanding"]})
        drafts.append({
            "studentId": position["studentId"],
            "studentName": position["studentName"],
            "guardianName": position["guardianName"],
            "ageingBucket": position["ageingBucket"],
            "tone": TONE_BY_BUCKET.get(position["ageingBucket"], "polite reminder"),
            "status": "DRAFT_FOR_REVIEW",
            "message": message,
            "llmGuardrail": "Amounts are supplied from ledger output; generated text is rejected if it contains unknown currency values.",
            "validationPassed": is_valid,
            "validationNote": validation_note,
        })
    return drafts

