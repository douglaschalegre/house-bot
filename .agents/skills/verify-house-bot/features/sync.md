# Finance synchronization

Ask Dindin to import a month, and distinguish confirmed completion from conflict or uncertainty.

## Sub-features

- `/sincronizar` defaults both options to the current period.
- Month only, year only, and both options override their respective defaults.
- Success includes the selected month/year and Dindin's confirmation timestamp.
- HTTP 409 reports an import already running.
- Timeouts, 502/504, network errors, and malformed confirmations report unconfirmed completion.
- Other failures report synchronization failure for the selected period.

## How to get to it (user POV)

Select `/sincronizar` in Discord, optionally choose month and two-digit year, and submit. It invokes the private Dindin service, which owns the import and database writes.

## Driving it with Discord computer use

Use an agreed import period and the intended private Dindin environment. Capture a read-only before snapshot, then submit `/sincronizar` with that period's actual options. Capture the deferred thinking state and final reply. Observe the POST to `/api/v1/finance/sync` in Dindin's request logs without recording the Authorization header. The body month format is `20YY-MM`.

Require `Finance data synchronized for MM/YY at ...` and a newly committed matching `synced_at` value in the database. Invoke `/historico` for the same period to prove the user's subsequent read sees the imported snapshot. A reply alone does not prove commit. For default/partial options, compare the effective period against the current Brazil-time month/year.

Conflict and uncertainty paths require genuine observed conditions or labelled boundary integration evidence from `tests/test_sync_client.py`; never manufacture failures against a shared production import. After an unconfirmed result, inspect the last-sync timestamp before retrying because the original import may still finish.

## Gotchas

- The request timeout is 240 seconds. Keep the user informed while waiting.
- The command's help text still says local import, but the code delegates to Dindin.
- The bot does not create or write finance tables.
- There is no dry-run. Do not use arbitrary historical periods on a shared service to generate evidence.
