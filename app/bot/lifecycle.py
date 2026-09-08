import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands

from app.finance.service import FinanceService
from app.jobs.monthly_finance_report import register_monthly_finance_report_job


logger = logging.getLogger(__name__)


def register_lifecycle(
    bot: commands.Bot,
    scheduler: AsyncIOScheduler,
    finance_service: FinanceService,
    shopping_channel_id: int,
    finance_channel_id: int,
) -> None:
    scheduler_started = False
    slash_commands_synced = False
    register_monthly_finance_report_job(
        scheduler, bot, finance_service, finance_channel_id
    )

    async def resolve_sync_guild() -> discord.Guild | None:
        channel = bot.get_channel(shopping_channel_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(shopping_channel_id)
            except discord.DiscordException:
                logger.exception("Unable to fetch shopping channel for slash sync")
                return None

        guild = getattr(channel, "guild", None)
        if guild is None:
            logger.error("Unable to resolve guild from shopping channel for slash sync")
        return guild

    @bot.event
    async def on_ready() -> None:
        nonlocal scheduler_started, slash_commands_synced
        logger.info("Logged in as %s", bot.user.name if bot.user else "unknown")

        if not scheduler_started:
            scheduler.start()
            scheduler_started = True
            logger.info("Scheduler started")

        if slash_commands_synced:
            return
        guild = await resolve_sync_guild()
        if guild is None:
            logger.warning("Slash command sync skipped; will retry on next ready event")
            return

        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        slash_commands_synced = True
        logger.info("Synced %s slash commands to guild %s", len(synced), guild.id)
