from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def load_json(name: str) -> list[dict[str, Any]]:
    with (DATA_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_seed_data() -> dict[str, list[dict[str, Any]]]:
    return {
        "students": load_json("students.json"),
        "fee_items": load_json("fee_structure.json"),
        "concessions": load_json("concessions.json"),
        "waivers": load_json("waivers.json"),
        "payments": load_json("payments.json"),
        "payment_plans": load_json("payment_plans.json"),
        "payment_history": load_json("payment_history.json"),
        "refunds": load_json("refunds.json"),
        "transfers": load_json("transfers.json"),
        "manual_adjustments": load_json("manual_adjustments.json"),
    }


def write_output(payload: dict[str, Any], output_path: Path | None = None) -> Path:
    path = output_path or BASE_DIR / "output.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path
