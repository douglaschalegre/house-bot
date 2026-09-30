---
name: verify-house-bot
description: Verify house-bot through real Discord messages and slash commands, with startup diagnostics, database evidence, and a feature map. Use after changing shopping commands, finance responses, Dindin sync, or bot lifecycle.
---

# Verify house-bot

Status: draft, awaiting a live Discord proof. Creation on 2026-09-30 found missing DATABASE_URL, DINDIN_URL, and DINDIN_SYNC_TOKEN. Ten existing unittest tests passed. This is not evidence of a working Discord session. See `artifacts/verify-house-bot/creation/`.

The primary user interface is Discord. There is no HTTP server, local CLI, or browser UI in this repo. `tests/` covers formatting, store ownership, lifecycle registration, and mocked Discord/Dindin boundaries. Those tests supplement a real Discord run; calling a registered callback directly is not a user-path proof.

## Launch

Run from the repository root. Python must be 3.12. Install the locked dependencies with `uv sync --locked`, then run:

```sh
mkdir -p artifacts/verify-house-bot/run
.venv/bin/python .agents/skills/verify-house-bot/scripts/preflight.py > artifacts/verify-house-bot/run/preflight.json
```

If preflight exits nonzero, fix the named settings in the local environment or `.env` without printing values. Required settings are DISCORD_TOKEN, DATABASE_URL, OPENAI_API_KEY, DINDIN_URL, and DINDIN_SYNC_TOKEN. GOOGLE_CREDENTIALS_PATH defaults to `credentials.json` relative to the root. Google credentials remain required even for shopping because `create_bot` builds all clients at startup. Do not invent service credentials or point imports at an unrelated server.

Before connecting, establish whether the same bot is already running locally, in Docker, or on the server. Local process inspection cannot rule out a remote instance. Reuse an existing instance only when its deployed commit is known and it is the intended verification target. Do not stop a user-owned instance or start a second session with its token.

The shopping channel is hardcoded as `1328396042689052682`, and the finance channel as `1328396082375295078` in `app/bot/__init__.py`. There are no channel override settings or dry-run flag. A different Discord token alone does not isolate these channels. Separate processes require distinct bot identities, test guild/channel configuration, databases, and Dindin services. Refuse concurrent drives of a shared instance.

If no other instance owns this identity and these channels are appropriate for the run, launch in an owned terminal/exec session:

```sh
uv run python main.py > artifacts/verify-house-bot/run/bot.log 2>&1
```

Retain the terminal session ID so cleanup can interrupt exactly this process. Ready means all three log entries appear without a later traceback: `Logged in as`, `Scheduler started`, and `Synced 8 slash commands to guild`. A login alone is insufficient. Startup creates shopping tables and initializes shopping state in the configured database; it is not read-only. It also syncs guild commands. There is no listening HTTP port. Teardown is Ctrl-C in the terminal session you started.

## Doctor

First run the executable preflight above. It reads local files and package metadata, prints only setting names and versions, and makes no network requests. It does not validate live credentials.

For the read-only live doctor, inspect the owned session and its `bot.log`, confirm its checkout/deployed commit, and open the configured shopping channel in an authenticated Discord user session. Confirm the expected bot is present and `/help` is offered by that bot in the slash command picker. This observation sends no message. Require a recent successful guild-sync log and no disconnect/startup error before driving. If using an existing remote instance, obtain equivalent process/log/build evidence from its owner. Do not infer readiness from another bot's autocomplete entry.

## Drive

Use computer-use `cua_repl` to operate Discord as a real user. Inventory available apps/tabs first; select the authenticated Discord window or tab. Do not use a user token, self-bot, fabricated interactions, internal callbacks, or test-only endpoints to bypass Discord.

Open channel `1328396042689052682` from the user's guild. Obtain a fresh accessibility snapshot and identify its message textbox by its actual channel label. Use the observed textbox, not guessed element indices. Type `/help`, inspect autocomplete, choose the `help` command owned by the expected bot, then submit. Typing a literal string is insufficient if Discord sends ordinary text instead of a slash interaction. Capture the submitted interaction and reply showing `Available Slash Commands:` and all eight commands. This is the lowest-impact initial proof and does not require changing shopping or finance records.

For other commands, follow every entry point and sub-feature in [features/README.md](features/README.md). Resolve fresh accessibility elements after each action. Command names and option names are stable handles; Discord's element indices and translated UI labels are not. For multiline shopping input, paste the complete text into the composer and inspect it before sending. The monthly report is an automatic channel message, not a slash command.

## Evidence

Store each run under a distinct `artifacts/verify-house-bot/<run-id>/` directory. The `run` directory in the commands above is for the first run; choose another name on repeats to avoid overwriting evidence. Retain preflight output, checkout commit, process/session ownership notes, startup logs, and a transcript containing the action, options, timestamp, channel, expected bot identity, and actual reply. Capture before/action/after accessibility snapshots or screenshots with the UI tool and record their artifact references in the transcript. Do not print `.env`, credential files, authorization headers, or token-bearing URLs.

Prove the user path and its resulting state. A final reply alone misses the submitted action. For shopping writes, compare read-only database queries and a subsequent `/lista`; for reset, prove the old list rows survive; for sync, verify the database committed timestamp and a subsequent finance command. The bot never writes finance tables. Capture minimum relevant financial data and keep evidence local.

Mocks may only replace existing production external boundaries, such as the Dindin HTTP client or OpenAI client, and must be labelled as partial integration evidence. The end-to-end deliverable requires a real Discord action. There is no safe dry-run mode: `/ordenar` calls a paid OpenAI API, `/sincronizar` asks Dindin to import, and the scheduled report sends `@everyone`. Document observed external calls and rows, not assumptions based on command names.

After one mapped feature passes, clean up, then confirm its evidence files still exist. Only then replace the draft status above with the proven feature, date, target build, and evidence path. Baseline tests or a failed preflight do not satisfy this step.

## Cleanup

Interrupt only the terminal/exec session launched for this run and confirm that session exits. Never kill by process name, stop an existing deployment, or use `docker compose down` against the user's instance. Run cleanup after failed startup and failed drives too. If startup failed before connecting, record that no running instance remains.

Close only tabs created for verification. Leave a reused Discord session intact. In a dedicated disposable database, remove run-owned scratch state only after evidence capture. Shared shopping lists have no item-removal command; `/zerar` preserves history and is not cleanup. Do not add synthetic items or reset a shared list without an agreed recovery plan. Remove only run-owned test messages if the user has authorized that cleanup. Keep all proof artifacts and diagnostic logs.

## Helpers

`scripts/preflight.py` is executable. Invoke it with `.venv/bin/python .agents/skills/verify-house-bot/scripts/preflight.py` or directly from an activated Python 3.12 environment. Exit 0 means local prerequisites passed, exit 1 means they failed. It never launches the bot, connects to services, or writes app data. There are no process managers or test routes hidden in this skill.

Use `/maintain-verification-skill` after app changes to audit the map and its instructions.
