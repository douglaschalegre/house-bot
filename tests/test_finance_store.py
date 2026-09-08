import unittest
import os

from app.database import Database
from app.domain.finance import FinanceEntry, FinancePeriod
from app.finance.store import FinanceStore


POSTGRES_TEST_URL = os.getenv("TEST_DATABASE_URL")


@unittest.skipUnless(POSTGRES_TEST_URL, "TEST_DATABASE_URL is not configured")
class FinanceStoreTest(unittest.TestCase):
    def test_snapshot_is_replaced_and_reloaded(self):
        store = FinanceStore(Database(POSTGRES_TEST_URL))
        period = FinancePeriod("99", "99")
        entry = FinanceEntry(period, "summary", "M6", "old")
        first_sync = store.save_snapshot(
            period, [["old"]], [["old"]], [entry]
        )
        second_sync = store.save_snapshot(
            period,
            [["new"]],
            [["new"]],
            [FinanceEntry(period, "summary", "M6", "new")],
        )

        self.assertIsNotNone(first_sync)
        self.assertIsNotNone(second_sync)
        snapshot = store.get_snapshot(period)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.summary_rows, [["new"]])
        self.assertEqual(snapshot.detail_rows, [["new"]])
        self.assertEqual(snapshot.synced_at, second_sync)
        self.assertEqual(
            store.get_entries(period),
            [FinanceEntry(period, "summary", "M6", "new")],
        )


if __name__ == "__main__":
    unittest.main()
