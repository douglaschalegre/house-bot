import asyncio
import logging

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from app.finance.service import FinancePeriod, FinanceService


logger = logging.getLogger(__name__)


def register_monthly_finance_report_job(
    scheduler: AsyncIOScheduler,
    bot: commands.Bot,
    finance_service: FinanceService,
    finance_channel_id: int,
) -> None:
    @scheduler.scheduled_job(
        CronTrigger(day="5"),
        id="monthly_finance_report",
    )
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
