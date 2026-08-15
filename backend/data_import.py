from __future__ import annotations

import ast
import json
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from typing import Any

from seed_data import load_seed_data


DATASET_ALIASES = {
    "students": "students",
    "fee_items": "fee_items",
    "feeitems": "fee_items",
    "fee_structure": "fee_items",
    "concessions": "concessions",
    "waivers": "waivers",
    "payments": "payments",
    "payment_plans": "payment_plans",
    "paymentplans": "payment_plans",
    "payment_history": "payment_history",
    "paymenthistory": "payment_history",
    "refunds": "refunds",
    "transfers": "transfers",
    "manual_adjustments": "manual_adjustments",
    "manualadjustments": "manual_adjustments",
}

STRUCTURED_FIELDS = {"lateFeePolicy", "installments", "paymentIds"}
INTEGER_FIELDS = {
    "amountPaise",
    "expectedPaise",
    "paidPaise",
    "totalAmountPaise",
    "dailyAmountPaise",
    "capPaise",
    "graceDays",
    "installmentNumber",
    "daysLate",
}


def canonical_dataset_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_").replace(" ", "_")
    key = normalized.replace("_", "")
    if normalized in DATASET_ALIASES:
        return DATASET_ALIASES[normalized]
    if key in DATASET_ALIASES:
        return DATASET_ALIASES[key]
    supported = ", ".join(sorted(set(DATASET_ALIASES.values())))
    raise ValueError(f"Unsupported dataset '{name}'. Use one of: {supported}.")


def _parse_structured_cell(value: Any, field: str) -> Any:
    if value in (None, ""):
        return [] if field in {"installments", "paymentIds"} else {}
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        raise ValueError(f"{field} must be JSON or spreadsheet text.")
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            raise ValueError(f"{field} is not valid structured data.") from error


def _coerce_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for field, value in row.items():
        if field is None:
            continue
        field = str(field).strip()
        if not field:
            continue
        if field in STRUCTURED_FIELDS:
            normalized[field] = _parse_structured_cell(value, field)
        elif field in INTEGER_FIELDS and value not in (None, ""):
            try:
                numeric_value = Decimal(str(value))
                if numeric_value != numeric_value.to_integral_value():
                    raise ValueError
                normalized[field] = int(numeric_value)
            except (InvalidOperation, TypeError, ValueError) as error:
                raise ValueError(f"{field} must be an integer value.") from error
        elif value is None:
            normalized[field] = ""
        else:
            normalized[field] = value
    return normalized


def merge_import_data(uploaded_datasets: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Merge selected spreadsheet datasets into the full deterministic seed set.

    A CSV is normally uploaded as ``payments``. A multi-sheet workbook can
    replace any supported dataset while preserving omitted supporting datasets,
    including transfer/refund/control fixtures needed by the finance workflow.
    """
    if not uploaded_datasets:
        raise ValueError("The upload did not contain any data rows.")

    merged = deepcopy(load_seed_data())
    total_rows = 0
    for raw_name, rows in uploaded_datasets.items():
        dataset_name = canonical_dataset_name(raw_name)
        if not isinstance(rows, list):
            raise ValueError(f"{raw_name} must contain a list of rows.")
        if len(rows) > 5_000:
            raise ValueError(f"{raw_name} exceeds the 5,000-row local import limit.")
        if any(not isinstance(row, dict) for row in rows):
            raise ValueError(f"{raw_name} contains an invalid row.")
        merged[dataset_name] = [_coerce_row(row) for row in rows]
        total_rows += len(rows)

    if total_rows == 0:
        raise ValueError("The upload did not contain any data rows.")
    return merged
