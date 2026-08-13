from __future__ import annotations

import json
import os
from typing import Any


def _prompt(position: dict[str, Any]) -> str:
    return f"""Draft a short school-fee reminder as JSON with keys subject, message, and tone.
Use only the supplied facts. Do not calculate, round, change, or add any monetary figure.
The exact amount must appear as {position['reminderAmount']} and the exact due date must appear as {position['reminderDueDate']}.
Do not mention a payment plan because this family has no approved plan. Keep it respectful and suitable for accounts-office review.
Facts:
student={position['studentName']}
guardian={position['guardianName']}
ageing_bucket={position['ageingBucket']}
days_overdue={position['daysOverdue']}
amount={position['reminderAmount']}
due_date={position['reminderDueDate']}
"""


def draft_with_gemini(position: dict[str, Any], model_name: str | None = None) -> dict[str, Any]:
    """Call Gemini through Vertex AI when explicitly enabled by the runner."""
    from google import genai
    from google.genai import types

    project = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "us-central1")
    if not project:
        raise RuntimeError("GCP_PROJECT_ID is required for Vertex AI Gemini drafting")
    client = genai.Client(vertexai=True, project=project, location=location)
    response = client.models.generate_content(
        model=model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        contents=_prompt(position),
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )
    raw = response.text or ""
    parsed = json.loads(raw)
    if not isinstance(parsed, dict) or not parsed.get("message"):
        raise ValueError("Gemini returned no usable reminder message")
    return parsed


def validate_draft(message: str, position: dict[str, Any]) -> tuple[bool, str]:
    """Reject drafts that alter the deterministic amount or due date."""
    import re

    amounts = set(re.findall(r"Rs\. [0-9,]+(?:\.[0-9]{2})?", message))
    expected_amount = position["reminderAmount"]
    if amounts != {expected_amount}:
        return False, f"Currency validation failed: expected only {expected_amount}, found {sorted(amounts)}"
    if position["reminderDueDate"] not in message:
        return False, f"Date validation failed: expected due date {position['reminderDueDate']}"
    return True, "Gemini wording passed deterministic amount and due-date validation."
