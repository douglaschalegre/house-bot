import unittest
from unittest.mock import patch

from app.database import Database
from app.finance.store import FinanceStore


class FinanceStoreTest(unittest.TestCase):
    def test_read_connection_does_not_create_tables(self):
        with patch("app.database.session.Base.metadata.create_all") as create:
            Database("sqlite://", create_shopping_tables=False)
        create.assert_not_called()
        self.assertFalse(hasattr(FinanceStore, "save_snapshot"))
