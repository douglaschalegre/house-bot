import unittest
import os

from app.finance.store import FinanceStore


POSTGRES_TEST_URL = os.getenv("TEST_DATABASE_URL")


@unittest.skipUnless(POSTGRES_TEST_URL, "TEST_DATABASE_URL is not configured")
class FinanceStoreTest(unittest.TestCase):
    def test_snapshot_is_replaced_and_reloaded(self):
        store = FinanceStore(POSTGRES_TEST_URL)
        first_sync = store.save_snapshot(
            "99", "99", [["old"]], [["old"]], [("summary", "M6", "old")]
        )
        second_sync = store.save_snapshot(
            "99", "99", [["new"]], [["new"]], [("summary", "M6", "new")]
        )

        self.assertIsNotNone(first_sync)
        self.assertIsNotNone(second_sync)
        self.assertEqual(
            store.get_snapshot("99", "99"),
            ([["new"]], [["new"]], second_sync),
        )
        self.assertEqual(store.get_entries("99", "99"), [("summary", "M6", "new")])


if __name__ == "__main__":
    unittest.main()
