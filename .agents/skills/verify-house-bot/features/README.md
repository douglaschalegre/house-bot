# House-bot feature map

The map describes the current Discord entry points. A claim covering a feature must exercise its listed sub-features or explicitly name the ones left unverified. The generator's initial live proof may cover only `/help`.

| Feature | Entry points | Observable proof |
| --- | --- | --- |
| [Help](help.md) | `/help` | Submitted interaction and reply listing eight commands |
| [Shopping](shopping.md) | Shopping channel text, `/lista`, `/ordenar`, `/zerar` | Persisted items, rendered list, sorted reply, retained history |
| [Finance views](finance.md) | `/dindin`, `/historico`, `/detalhado` | Correct period, snapshot values and last-sync timestamp |
| [Finance synchronization](sync.md) | `/sincronizar` with optional month/year | Dindin confirmation and committed database snapshot |
| [Monthly report](monthly-report.md) | Automatic report on day 5 | One report in finance channel with current Sheets summary |

Source owners are `app/bot/__init__.py`, `app/bot/shopping_commands.py`, `app/bot/finance_commands.py`, and `app/jobs/monthly_finance_report.py`. There is no `!help` prefix handler, removal command, or manual monthly-report command.
