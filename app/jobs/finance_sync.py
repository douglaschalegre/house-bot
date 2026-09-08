import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.finance.service import FinancePeriod, FinanceService


logger = logging.getLogger(__name__)


async def sync_current_finance(finance_service: FinanceService) -> None:
    period = FinancePeriod.current()
    try:
        synced_at = await asyncio.to_thread(finance_service.synchronize, period)
        logger.info(
            "Finance sync completed for %s/%s at %s",
            period.month,
            period.year,
            synced_at,
        )
    except Exception:
        logger.exception(
            "Failed to synchronize finance data for %s/%s",
            period.month,
            period.year,
        )


def register_finance_sync_job(
    scheduler: AsyncIOScheduler, finance_service: FinanceService
) -> None:
    @scheduler.scheduled_job(
        IntervalTrigger(hours=1),
        id="finance_sync_hourly",
    )
    async def sync_finance_hourly() -> None:
        await sync_current_finance(finance_service)
