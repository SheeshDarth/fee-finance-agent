import unittest
from datetime import date

from agent_runner import build_finance_run
from data_import import merge_import_data


class DataImportTests(unittest.TestCase):
    def test_payment_csv_merge_preserves_omitted_datasets(self):
        data = merge_import_data({
            "payments": [{
                "paymentId": "P-LOCAL-001",
                "studentId": "S001",
                "invoiceRef": "F001",
                "date": "2026-08-01",
                "amountPaise": "2000000",
                "mode": "UPI",
                "rawNarration": "LOCAL IMPORT",
            }],
        })

        self.assertEqual(data["payments"][0]["amountPaise"], 2_000_000)
        self.assertEqual(len(data["students"]), 4)
        self.assertEqual(data["refunds"][0]["refundId"], "R001")

    def test_workflow_changes_when_payment_csv_is_imported(self):
        baseline = build_finance_run(date(2026, 8, 13), use_llm=False)
        imported = build_finance_run(date(2026, 8, 13), use_llm=False, override_data={
            "payments": [{
                "paymentId": "P-LOCAL-001",
                "studentId": "S001",
                "invoiceRef": "F001",
                "date": "2026-08-01",
                "amountPaise": 2_000_000,
                "mode": "UPI",
                "rawNarration": "LOCAL IMPORT",
            }],
        })

        self.assertNotEqual(
            baseline["dashboard"]["totalOutstandingPaise"],
            imported["dashboard"]["totalOutstandingPaise"],
        )

    def test_invalid_dataset_name_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported dataset"):
            merge_import_data({"mystery_sheet": [{"id": "1"}]})

    def test_fractional_paise_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "amountPaise must be an integer"):
            merge_import_data({
                "payments": [{"paymentId": "P-LOCAL-002", "amountPaise": "120.5"}],
            })


if __name__ == "__main__":
    unittest.main()
