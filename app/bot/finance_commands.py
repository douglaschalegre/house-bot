import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from app.bot.discord_utils import safe_defer, safe_followup_send
from app.finance.service import FinancePeriod, FinanceService


logger = logging.getLogger(__name__)


def register_finance_commands(
    bot: commands.Bot, finance_service: FinanceService
) -> None:
    async def send_finance_response(
        interaction: discord.Interaction,
        period: FinancePeriod | None = None,
        detailed: bool = False,
    ) -> None:
        try:
            message = await asyncio.to_thread(
                finance_service.response, period or FinancePeriod.current(), detailed
            )
        except Exception:
            logger.exception("Failed to build finance response")
            await safe_followup_send(
                interaction, "An error occurred while reading finance data."
            )
            return
        await safe_followup_send(interaction, message)

    @bot.tree.command(
        name="dindin",
        description=(
            "Shows the current month's financial summary including salaries "
            "and contributions."
        ),
    )
    async def dindin_command(interaction: discord.Interaction) -> None:
        if await safe_defer(interaction):
            await send_finance_response(interaction)

    @bot.tree.command(
        name="sincronizar",
        description="Synchronizes a finance period from Google Sheets to the local database.",
    )
    @app_commands.describe(month="Month number from 1 to 12", year="Two-digit year (0-99)")
    async def sincronizar_command(
        interaction: discord.Interaction,
        month: app_commands.Range[int, 1, 12] | None = None,
        year: app_commands.Range[int, 0, 99] | None = None,
    ) -> None:
        if not await safe_defer(interaction):
            return
        current = FinancePeriod.current()
        period = FinancePeriod(
            month=f"{month:02d}" if month is not None else current.month,
            year=f"{year:02d}" if year is not None else current.year,
        )
        try:
            synced_at = await asyncio.to_thread(finance_service.synchronize, period)
        except Exception:
            logger.exception(
                "Failed to synchronize finance data for %s/%s",
                period.month,
                period.year,
            )
            await safe_followup_send(
                interaction,
                f"Finance synchronization failed for {period.month}/{period.year}.",
            )
            return
        await safe_followup_send(
            interaction,
            f"Finance data synchronized for {period.month}/{period.year} at {synced_at}.",
        )

    @bot.tree.command(
        name="historico", description="Shows financial data for a specific month and year."
    )
    @app_commands.describe(month="Month number from 1 to 12", year="Two-digit year (0-99)")
    async def historico_command(
        interaction: discord.Interaction,
        month: app_commands.Range[int, 1, 12],
        year: app_commands.Range[int, 0, 99],
    ) -> None:
        if await safe_defer(interaction):
            await send_finance_response(
                interaction, FinancePeriod(month=f"{month:02d}", year=f"{year:02d}")
            )

    @bot.tree.command(
        name="detalhado",
        description=(
            "Shows a detailed view of the current month's finances, "
            "including all expenses."
        ),
    )
    async def detalhado_command(interaction: discord.Interaction) -> None:
        if await safe_defer(interaction):
            await send_finance_response(interaction, detailed=True)

