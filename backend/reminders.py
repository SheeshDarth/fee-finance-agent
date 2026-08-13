from __future__ import annotations

from typing import Any

from llm_drafter import draft_with_gemini, validate_draft


TONE_BY_BUCKET = {
    "0-30": "polite reminder",
    "31-60": "firm but respectful reminder",
    "60+": "urgent formal reminder",
}


def _template_message(position: dict[str, Any]) -> str:
    tone = TONE_BY_BUCKET.get(position["ageingBucket"], "polite reminder")
    return (
        f"Dear {position['guardianName']}, this is a {tone} for {position['studentName']}'s "
        f"school fee balance of {position['reminderAmount']}. The instalment was due on "
        f"{position['reminderDueDate']} and is now {position['daysOverdue']} days overdue. "
        "Please treat this as a draft notice for accounts-office review before any parent "
        "communication is sent."
    )


def draft_reminders(positions: list[dict[str, Any]], use_llm: bool = False) -> list[dict[str, Any]]:
    drafts = []
    for position in positions:
        if not position["shouldDraftReminder"]:
            continue
        generation_source = "DETERMINISTIC_TEMPLATE"
        model = None
        generation_error = None
        try:
            generated = draft_with_gemini(position) if use_llm else None
            message = generated["message"] if generated else _template_message(position)
            model = "Gemini" if generated else None
            generation_source = "GEMINI" if generated else generation_source
        except Exception as error:
            message = _template_message(position)
            generation_error = str(error)
            generation_source = "DETERMINISTIC_FALLBACK"
        is_valid, validation_note = validate_draft(message, position)
        if is_valid and generation_source != "GEMINI":
            validation_note = "Deterministic template passed amount and due-date validation."
        drafts.append({
            "studentId": position["studentId"],
            "studentName": position["studentName"],
            "guardianName": position["guardianName"],
            "ageingBucket": position["ageingBucket"],
            "tone": TONE_BY_BUCKET.get(position["ageingBucket"], "polite reminder"),
            "status": "DRAFT_FOR_REVIEW",
            "message": message,
            "generationSource": generation_source,
            "model": model,
            "generationError": generation_error,
            "dueDate": position["reminderDueDate"],
            "amount": position["reminderAmount"],
            "llmGuardrail": "Amounts and due dates are supplied from ledger output; generated text is rejected if it changes either value.",
            "validationPassed": is_valid,
            "validationNote": validation_note,
        })
    return drafts
