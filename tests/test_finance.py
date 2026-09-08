import unittest

from app.finance import (
    FinancePeriod,
    FinanceSnapshot,
    FinanceService,
    format_detailed_expenses,
    format_finance_summary,
    normalize_row,
)


class FinanceFormattingTest(unittest.TestCase):
    period = FinancePeriod("03", "24")

    def test_normalize_row_fills_missing_values(self):
        self.assertEqual(normalize_row([" Douglas ", None]), ["Douglas", "-", "-"])

    def test_format_detailed_expenses_skips_empty_rows(self):
        result = format_detailed_expenses(
            [["100", "10%", "50"], ["200", "20%", "100"], ["300", "30%", "150"]],
            [["Rent", "1000", "fixed"], ["", "", ""], ["Food", "200", "monthly"]],
            self.period,
        )
        self.assertIn("Rent", result)
        self.assertIn("Food", result)
        self.assertEqual(len(result.splitlines()), 9)


class FinanceServiceTest(unittest.TestCase):
    def test_response_uses_snapshot_and_formats_sync_time(self):
        class Store:
            def get_snapshot(self, period):
                return FinanceSnapshot(
                    period=period,
                    summary_rows=[["100", "10%", "50"]] * 3,
                    detail_rows=[],
                    synced_at="2026-09-07T12:00:00+00:00",
                )

        class Reader:
            pass

        response = FinanceService(Store(), Reader()).response(
            FinancePeriod("09", "26")
        )

        self.assertIn("Sheet: Expenses 09/26", response)
        self.assertIn("07/09/2026 09:00:00", response)


if __name__ == "__main__":
    unittest.main()
