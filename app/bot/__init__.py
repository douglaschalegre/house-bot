from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord
import gspread
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI

from app.config import Settings
from app.database import Database
from app.finance.service import FinanceService, FinanceSheetReader
from app.bot.finance_commands import register_finance_commands
from app.bot.lifecycle import register_lifecycle
from app.bot.shopping_commands import register_shopping_commands

if TYPE_CHECKING:
    from app.finance.store import FinanceStore
    from app.shopping.store import ShoppingStore


logger = logging.getLogger(__name__)

SHOPPING_CHANNEL_ID = 1328396042689052682
FINANCE_CHANNEL_ID = 1328396082375295078


def create_bot(settings: Settings) -> commands.Bot:
    from app.finance.store import FinanceStore
    from app.shopping.store import ShoppingStore

    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    database = Database(settings.database_url)
    shopping_store = ShoppingStore(database)
    finance_service = FinanceService(
        FinanceStore(database),
        FinanceSheetReader(_create_sheets_client(settings)),
    )
    openai_client = OpenAI(api_key=settings.openai_api_key)
    scheduler = AsyncIOScheduler()

    _log_shopping_store_status(shopping_store)
    register_shopping_commands(
        bot, shopping_store, openai_client, SHOPPING_CHANNEL_ID
    )
    register_finance_commands(bot, finance_service)
    register_lifecycle(
        bot,
        scheduler,
        finance_service,
        SHOPPING_CHANNEL_ID,
        FINANCE_CHANNEL_ID,
    )
    _register_shopping_list_reset_command(bot, shopping_store)
    _register_help_command(bot)
    return bot


def _create_sheets_client(settings: Settings):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        str(settings.credentials_path),
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(credentials)


def _log_shopping_store_status(store: ShoppingStore) -> None:
    status = store.get_status()
    logger.info(
        "Shopping store initialized: db_path=%s current_list_id=%s "
        "current_item_count=%s max_list_id=%s",
        status["db_path"],
        status["current_list_id"],
        status["current_item_count"],
        status["max_list_id"],
    )


def _register_shopping_list_reset_command(
    bot: commands.Bot, store: ShoppingStore
) -> None:
    @bot.tree.command(
        name="zerar", description="Starts a new shopping list while keeping history."
    )
    async def zerar_command(interaction: discord.Interaction) -> None:
        list_id = await asyncio.to_thread(store.advance_list)
        await interaction.response.send_message(
            f"[ ! ] Started a new shopping list with list_id {list_id}."
        )


def _register_help_command(bot: commands.Bot) -> None:
    @bot.tree.command(name="help", description="Shows all available slash commands.")
    async def help_command(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(build_help_text())


def build_help_text() -> str:
    return """
**Available Slash Commands:**

`/dindin`
Shows the current month's financial summary including salaries and contributions.

`/detalhado`
Shows a detailed view of the current month's finances, including all expenses.

`/sincronizar month:<1-12> year:<0-99>`
Synchronizes a finance period from Google Sheets to the local database.

`/historico month:<1-12> year:<0-99>`
Shows financial data for a specific month and year.
Example: `/historico month:3 year:24` (for March 2024)

**Shopping List Features:**
- Add items by typing them in the shopping list channel
- Each line will be treated as a separate item
- Bot messages are ignored

`/lista`
Shows the current shopping list.

`/zerar`
Starts a new shopping list while keeping history.

`/ordenar`
Organizes the shopping list using GPT-4.

`/help`
Shows this help message.
"""
