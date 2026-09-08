import unittest

from app.finance import (
    FinancePeriod,
    FinanceService,
    annotate_cells,
    column_name,
    format_detailed_expenses,
    format_finance_summary,
    normalize_row,
)


class FinanceFormattingTest(unittest.TestCase):
    period = FinancePeriod("03", "24")

    def test_column_name_converts_spreadsheet_columns(self):
        self.assertEqual(column_name(1), "A")
        self.assertEqual(column_name(26), "Z")
        self.assertEqual(column_name(27), "AA")

    def test_annotate_cells_preserves_section_and_coordinates(self):
        self.assertEqual(
            annotate_cells("summary", [["a", None], ["b", 2]], "M6"),
            [
                ("summary", "M6", "a"),
                ("summary", "N6", ""),
                ("summary", "M7", "b"),
                ("summary", "N7", "2"),
            ],
        )

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
            def get_snapshot(self, month, year):
                return (
                    [["100", "10%", "50"]] * 3,
                    [],
                    "2026-09-07T12:00:00+00:00",
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
