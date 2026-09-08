import unittest

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.bot.lifecycle import register_lifecycle


class Bot:
    def event(self, callback):
        return callback


class LifecycleJobsTest(unittest.TestCase):
    def test_registers_hourly_sync_and_monthly_report(self):
        scheduler = AsyncIOScheduler()

        register_lifecycle(Bot(), scheduler, object(), 1, 2)

        self.assertEqual(
            {job.id for job in scheduler.get_jobs()},
            {"finance_sync_hourly", "monthly_finance_report"},
        )
        self.assertEqual(
            str(scheduler.get_job("finance_sync_hourly").trigger),
            "interval[1:00:00]",
        )
        self.assertEqual(
            str(scheduler.get_job("monthly_finance_report").trigger),
            "cron[day='5']",
        )


if __name__ == "__main__":
    unittest.main()
