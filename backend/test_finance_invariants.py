import unittest
from datetime import date

from ledger import calculate_positions
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
            reconciliation_results=self.reconciliation,
            as_of=date(2026, 8, 13),
        )
        kabir = next(row for row in positions if row["studentId"] == "S003")
        self.assertEqual(kabir["paidPaise"], 0)
        self.assertNotIn("P003", kabir["trace"]["paymentIds"])
        self.assertIn("P003", kabir["trace"]["pendingReviewPaymentIds"])
        self.assertEqual(dashboard["totalCollectedPaise"], 5_550_000)
        self.assertEqual(dashboard["pendingReviewPaise"], 1_900_000)

    def test_dashboard_totals_reconcile(self):
        _, dashboard = calculate_positions(
            students=self.data["students"],
            fee_items=self.data["fee_items"],
            concessions=self.data["concessions"],
            waivers=self.data["waivers"],
            payments=self.data["payments"],
            payment_plans=self.data["payment_plans"],
            reconciliation_results=self.reconciliation,
            as_of=date(2026, 8, 13),
        )
        self.assertEqual(
            dashboard["totalNetDuePaise"],
            dashboard["totalCollectedPaise"] + dashboard["totalOutstandingPaise"],
        )
        self.assertEqual(
            sum(row["amountPaise"] for row in dashboard["ageingBuckets"].values()),
            dashboard["totalOverduePaise"],
        )


if __name__ == "__main__":
    unittest.main()
