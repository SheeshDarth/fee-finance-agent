import unittest
from datetime import date

from ledger import calculate_positions
from ledger import build_worklist
from reconciliation import reconcile_payments
from seed_data import load_seed_data


class FinanceInvariantTests(unittest.TestCase):
    def setUp(self):
        self.data = load_seed_data()
        self.reconciliation = reconcile_payments(
            self.data["students"], self.data["fee_items"], self.data["payments"]
        )

    def test_review_payments_are_excluded_from_verified_ledger(self):
        positions, dashboard = calculate_positions(
            students=self.data["students"],
            fee_items=self.data["fee_items"],
            concessions=self.data["concessions"],
            waivers=self.data["waivers"],
            payments=self.data["payments"],
            payment_plans=self.data["payment_plans"],
            payment_history=self.data["payment_history"],
            reconciliation_results=self.reconciliation,
            as_of=date(2026, 8, 13),
        )
        kabir = next(row for row in positions if row["studentId"] == "S003")
        self.assertEqual(kabir["paidPaise"], 0)
        self.assertNotIn("P003", kabir["trace"]["paymentIds"])
        self.assertIn("P003", kabir["trace"]["pendingReviewPaymentIds"])
        self.assertGreater(dashboard["totalLateFeePaise"], 0)
        self.assertEqual(dashboard["pendingReviewPaise"], 1_900_000)

    def test_dashboard_totals_reconcile(self):
        _, dashboard = calculate_positions(
            students=self.data["students"],
            fee_items=self.data["fee_items"],
            concessions=self.data["concessions"],
            waivers=self.data["waivers"],
            payments=self.data["payments"],
            payment_plans=self.data["payment_plans"],
            payment_history=self.data["payment_history"],
            reconciliation_results=self.reconciliation,
            as_of=date(2026, 8, 13),
        )
        self.assertEqual(
            dashboard["totalNetDuePaise"],
            dashboard["totalCollectedPaise"] + dashboard["totalOutstandingPaise"],
        )
        self.assertEqual(
            sum(row["amountPaise"] for bucket, row in dashboard["ageingBuckets"].items() if bucket != "NOT_OVERDUE"),
            dashboard["totalOverduePaise"],
        )

    def test_plan_schedule_and_history_are_visible(self):
        positions, _ = calculate_positions(
            students=self.data["students"], fee_items=self.data["fee_items"],
            concessions=self.data["concessions"], waivers=self.data["waivers"],
            payments=self.data["payments"], payment_plans=self.data["payment_plans"],
            payment_history=self.data["payment_history"],
            reconciliation_results=self.reconciliation, as_of=date(2026, 8, 13),
        )
        kabir = next(row for row in positions if row["studentId"] == "S003")
        self.assertEqual(len(kabir["paymentPlan"]["installments"]), 2)
        self.assertEqual(kabir["planCompliance"], "OVERDUE")
        self.assertEqual(kabir["paymentHistory"]["missedPaymentCount"], 1)

    def test_worklist_includes_history_score_components(self):
        positions, _ = calculate_positions(
            students=self.data["students"], fee_items=self.data["fee_items"],
            concessions=self.data["concessions"], waivers=self.data["waivers"],
            payments=self.data["payments"], payment_plans=self.data["payment_plans"],
            payment_history=self.data["payment_history"],
            reconciliation_results=self.reconciliation, as_of=date(2026, 8, 13),
        )
        kabir = next(row for row in build_worklist(positions) if row["studentId"] == "S003")
        self.assertGreater(kabir["scoreBreakdown"]["missedHistory"], 0)
        self.assertIn("missed", kabir["reason"])


if __name__ == "__main__":
    unittest.main()
