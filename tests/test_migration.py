import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.migrate_sqlite_to_postgres import sqlite_table_exists


class MigrationTest(unittest.TestCase):
    def test_detects_finance_tables_from_existing_sqlite_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "shopping.sqlite3"
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE finance_snapshots (id INTEGER)")

                self.assertTrue(sqlite_table_exists(connection, "finance_snapshots"))
                self.assertFalse(sqlite_table_exists(connection, "finance_entries"))


if __name__ == "__main__":
    unittest.main()
