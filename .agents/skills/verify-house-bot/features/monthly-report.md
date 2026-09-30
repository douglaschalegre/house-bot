# Monthly finance report

Receive the scheduled current-month summary in the finance channel on day 5.

## Sub-features

- Startup registers only the `monthly_finance_report` scheduler job.
- The cron trigger runs on day 5 in the scheduler's default timezone.
- The report reads `M6:O8` from `Expenses MM/YY` in Google Sheets.
- It resolves the finance channel from cache or fetch and sends a report with an everyone mention.
- Reconnection starts the scheduler and syncs commands only once for that process.

## How to get to it (user POV)

Open finance channel `1328396082375295078` when the report is scheduled. There is no manual report slash command.

## Driving it with Discord computer use

Observe the real scheduled event on day 5 and capture the channel before/after, report timestamp, and startup log for the same process. Compare the rendered current-month summary to Google Sheets range `M6:O8`. Require one `@everyone` report containing `Sheet: Expenses MM/YY`, names, and contribution values in the expected channel.

For a run outside the scheduled date, record this feature as unverified live. `tests/test_lifecycle_jobs.py` proves job registration only. Calling the job function directly or changing the machine clock is not the normal user path. Reconnection coverage needs a controlled dedicated environment with logs demonstrating no second scheduler start or slash sync.

## Gotchas

- The scheduler receives no explicit timezone in code; Docker sets TZ to America/Sao_Paulo. Verify the actual target timezone rather than assuming local behavior matches Docker.
- Finance period calculation uses America/Sao_Paulo regardless of scheduler timezone.
- This path reads Google Sheets, not imported database snapshots.
- It explicitly allows everyone mentions. Do not trigger the job manually in the shared channel for testing.
