import asyncio
import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from app.finance.service import FinancePeriod, FinanceService


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

    @scheduler.scheduled_job(CronTrigger(day="5"))
    async def send_month_finance_data() -> None:
        period = FinancePeriod.current()
        try:
            table = await asyncio.to_thread(finance_service.current_summary, period)
            channel = bot.get_channel(finance_channel_id)
            if channel is None:
                channel = await bot.fetch_channel(finance_channel_id)
            await channel.send(
                f"@everyone\n```\n{table}\n```",
                allowed_mentions=discord.AllowedMentions(everyone=True),
            )
        except Exception:
            logger.exception(
                "Failed to send scheduled finance data for %s/%s",
                period.month,
                period.year,
            )

