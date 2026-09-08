import io
import json
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from app.domain.finance import FinancePeriod
from app.finance.sync_client import FinanceSyncClient, SyncInProgress, SyncUnconfirmed


class SyncClientTest(unittest.TestCase):
    def setUp(self):
        self.client = FinanceSyncClient("http://dindin-api:8080", "test-token")
        self.client.opener = Mock()
        self.period = FinancePeriod("03", "24")

    def test_success_contract(self):
        response = io.BytesIO(
            json.dumps({"month": "2024-03", "syncedAt": "committed"}).encode()
        )
        self.client.opener.open.return_value = response
        self.assertEqual(self.client.synchronize(self.period), "committed")
        request = self.client.opener.open.call_args.args[0]
        self.assertEqual(json.loads(request.data), {"month": "2024-03"})
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        self.assertEqual(request.full_url, "http://dindin-api:8080/api/v1/finance/sync")

    def test_conflict_and_failure(self):
        for status, exception in (
            (409, SyncInProgress),
            (503, RuntimeError),
            (403, RuntimeError),
            (504, SyncUnconfirmed),
        ):
            self.client.opener.open.side_effect = HTTPError(
                "url", status, "error", {}, None
            )
            with self.assertRaises(exception):
                self.client.synchronize(self.period)

    def test_timeout_is_unconfirmed(self):
        for error in (TimeoutError(), URLError(TimeoutError())):
            self.client.opener.open.side_effect = error
            with self.assertRaises(SyncUnconfirmed):
                self.client.synchronize(self.period)

    def test_financial_reads_and_shopping_startup(self):
        from app.database import Database
        from app.database.models.shopping import ShoppingItemRecord, ShoppingStateRecord

        with patch("app.database.session.Base.metadata.create_all") as create:
            Database("sqlite://")
        self.assertEqual(
            set(create.call_args.kwargs["tables"]),
            {ShoppingItemRecord.__table__, ShoppingStateRecord.__table__},
        )


class FinanceCommandTest(unittest.IsolatedAsyncioTestCase):
    async def test_sync_messages(self):
        from unittest.mock import AsyncMock

        from app.bot.finance_commands import register_finance_commands

        class Tree:
            def __init__(self):
                self.commands = {}

            def command(self, *, name, description):
                def register(callback):
                    self.commands[name] = callback
                    return callback

                return register

        bot = Mock()
        bot.tree = Tree()
        sync = Mock()
        register_finance_commands(bot, Mock(), sync)
        for outcome, text in (
            ("committed", "synchronized"),
            (SyncInProgress(), "already synchronizing"),
            (SyncUnconfirmed(), "did not confirm"),
            (RuntimeError(), "failed"),
        ):
            sync.synchronize.side_effect = (
                outcome if isinstance(outcome, Exception) else None
            )
            sync.synchronize.return_value = outcome
            with (
                patch(
                    "app.bot.finance_commands.safe_defer",
                    new=AsyncMock(return_value=True),
                ),
                patch(
                    "app.bot.finance_commands.safe_followup_send", new=AsyncMock()
                ) as send,
            ):
                await bot.tree.commands["sincronizar"](Mock(), month=3, year=24)
                self.assertIn(text, send.call_args.args[1])
                self.assertEqual(
                    sync.synchronize.call_args.args[0], FinancePeriod("03", "24")
                )
