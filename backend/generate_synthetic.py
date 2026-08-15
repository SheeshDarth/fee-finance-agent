import json
import pandas as pd
from pathlib import Path
import copy

BASE_DIR = Path(__file__).resolve().parent

def generate_synthetic():
    # Load original JSON files
    sheets = {
        "students": json.loads((BASE_DIR / "data/students.json").read_text(encoding="utf-8")),
        "fee_items": json.loads((BASE_DIR / "data/fee_structure.json").read_text(encoding="utf-8")),
        "concessions": json.loads((BASE_DIR / "data/concessions.json").read_text(encoding="utf-8")),
        "waivers": json.loads((BASE_DIR / "data/waivers.json").read_text(encoding="utf-8")),
        "payments": json.loads((BASE_DIR / "data/payments.json").read_text(encoding="utf-8")),
        "payment_plans": json.loads((BASE_DIR / "data/payment_plans.json").read_text(encoding="utf-8")),
        "payment_history": json.loads((BASE_DIR / "data/payment_history.json").read_text(encoding="utf-8")),
    }

    # Make some noticeable changes for the demo
    # 1. Change a student's name
    sheets["students"][0]["name"] = "Aarav Sharma (SYNTHETIC DATA DEMO)"
    
    # 2. Add a massive fake payment to prove it recalculates
    sheets["payments"].append({
        "paymentId": "PAY-SYNTHETIC-999",
        "date": "2026-08-14",
        "amountPaise": 50000000, # Rs 5,00,000
        "mode": "BANK_TRANSFER",
        "reference": "SYNTH-DEMO-TXN",
        "matchedStudentId": "S001",
        "confidence": "CONFIDENT",
        "reason": "Synthetic huge payment for demo"
    })

    # Write to Excel
    out_path = BASE_DIR.parent / "synthetic_demo.xlsx"
    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        for sheet_name, data in sheets.items():
            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
    print(f"Generated {out_path}")

if __name__ == "__main__":
    generate_synthetic()
