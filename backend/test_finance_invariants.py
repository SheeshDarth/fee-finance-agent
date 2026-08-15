import unittest
from datetime import date

from ledger import calculate_positions
from ledger import build_worklist
from llm_drafter import validate_draft
from agent_runner import build_finance_run
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

    def test_reminder_validator_rejects_changed_money(self):
        positions, _ = calculate_positions(
            students=self.data["students"], fee_items=self.data["fee_items"],
            concessions=self.data["concessions"], waivers=self.data["waivers"],
            payments=self.data["payments"], payment_plans=self.data["payment_plans"],
            payment_history=self.data["payment_history"],
            reconciliation_results=self.reconciliation, as_of=date(2026, 8, 13),
        )
        aarav = next(row for row in positions if row["studentId"] == "S001")
        valid, _ = validate_draft(f"Balance Rs. 99,999 due {aarav['reminderDueDate']}", aarav)
        self.assertFalse(valid)

    def test_reminder_validator_accepts_live_model_punctuation(self):
        positions, _ = calculate_positions(
            students=self.data["students"], fee_items=self.data["fee_items"],
            concessions=self.data["concessions"], waivers=self.data["waivers"],
            payments=self.data["payments"], payment_plans=self.data["payment_plans"],
            payment_history=self.data["payment_history"],
            reconciliation_results=self.reconciliation, as_of=date(2026, 8, 13),
        )
        aarav = next(row for row in positions if row["studentId"] == "S001")
        valid, note = validate_draft(
            f"The amount due is {aarav['reminderAmount']}, which was due on {aarav['reminderDueDate']}. Then contact the accounts office.",
            aarav,
        )
        self.assertTrue(valid, note)

    def test_audit_records_approval_authority(self):
        payload = build_finance_run(date(2026, 8, 13), use_llm=False)
        event_types = {event["eventType"] for event in payload["auditEvents"]}
        self.assertTrue({"CONCESSION_APPROVED", "WAIVER_APPROVED", "PAYMENT_PLAN_APPROVED"}.issubset(event_types))
        plan_event = next(event for event in payload["auditEvents"] if event["eventType"] == "PAYMENT_PLAN_APPROVED")
        self.assertEqual(plan_event["actor"], "Accounts Head")

    def test_agent_decisions_are_explainable_and_preserve_money(self):
        payload = build_finance_run(date(2026, 8, 13), use_llm=False)
        dashboard = payload["dashboard"]
        self.assertEqual(dashboard["totalNetDuePaise"], 12_133_500)
        self.assertEqual(dashboard["totalCollectedPaise"], 5_550_000)
        self.assertEqual(dashboard["totalOutstandingPaise"], 6_583_500)

        decisions = {row["studentId"]: row for row in payload["agentDecisions"]}
        self.assertEqual(set(decisions), {"S001", "S002", "S003", "S004"})
        self.assertTrue(all(row["reason"] for row in decisions.values()))
        self.assertEqual(decisions["S001"]["chosenAction"], "DRAFT_REMINDER")
        self.assertEqual(decisions["S002"]["chosenAction"], "DRAFT_REMINDER")
        self.assertEqual(decisions["S003"]["chosenAction"], "ESCALATE_FOR_REVIEW")
        self.assertEqual(decisions["S004"]["chosenAction"], "ESCALATE_FOR_REVIEW")

    def test_agent_escalations_keep_ambiguous_payments_visible(self):
        payload = build_finance_run(date(2026, 8, 13), use_llm=False)
        escalations = {row["escalationId"]: row for row in payload["escalations"]}
        self.assertIn("PAYMENT-P003", escalations)
        self.assertIn("PAYMENT-P004", escalations)
        self.assertNotIn("PLAN-S003", escalations)
        self.assertEqual(
            next(row for row in payload["agentDecisions"] if row["studentId"] == "S003")["relatedPaymentIds"],
            ["P003"],
        )
        audit_types = {event["eventType"] for event in payload["auditEvents"]}
        self.assertIn("CASE_ESCALATED_FOR_REVIEW", audit_types)
        self.assertIn("REMINDER_DECISION_MADE", audit_types)

    def test_cash_forecast_is_explicitly_low_confidence_and_does_not_change_ledger(self):
        payload = build_finance_run(date(2026, 8, 13), use_llm=False)
        forecast = payload["forecast"]["summary"]
        self.assertEqual(payload["dashboard"]["totalNetDuePaise"], 12_133_500)
        self.assertEqual(forecast["historicalRecordCount"], 5)
        self.assertEqual(forecast["forecastConfidence"], "LOW")
        self.assertEqual(forecast["expectedCashInflowPaise"], 1_534_682)
        self.assertIn("S003", forecast["likelyDelayStudentIds"])

    def test_leakage_scan_creates_review_findings_without_mutating_money(self):
        payload = build_finance_run(date(2026, 8, 13), use_llm=False)
        findings = {row["findingId"]: row for row in payload["leakage"]["findings"]}
        self.assertIn("LEAK-PAYMENT-P003", findings)
        self.assertIn("LEAK-PAYMENT-P004", findings)
        self.assertIn("LEAK-TRANSFER-T001", findings)
        self.assertIn("LEAK-REFUND-AUTH-R001", findings)
        self.assertIn("LEAK-ADJUSTMENT-A001", findings)
        self.assertEqual(payload["leakage"]["summary"]["highSeverityCount"], 4)
        self.assertEqual(payload["dashboard"]["totalOutstandingPaise"], 6_583_500)
        self.assertEqual(len(payload["reminderDrafts"]), 2)


if __name__ == "__main__":
    unittest.main()
