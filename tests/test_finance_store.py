import tempfile
import unittest
from pathlib import Path

from app.finance_store import FinanceStore


class FinanceStoreTest(unittest.TestCase):
    def test_snapshot_is_replaced_and_reloaded(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FinanceStore(str(Path(directory) / "finance.sqlite3"))
            first_sync = store.save_snapshot("09", "26", [["old"]], [["old"]])
            second_sync = store.save_snapshot("09", "26", [["new"]], [["new"]])

            self.assertIsNotNone(first_sync)
            self.assertIsNotNone(second_sync)
            self.assertEqual(
                store.get_snapshot("09", "26"),
                ([["new"]], [["new"]], second_sync),
            )
            self.assertIsNone(store.get_snapshot("08", "26"))


if __name__ == "__main__":
    unittest.main()
