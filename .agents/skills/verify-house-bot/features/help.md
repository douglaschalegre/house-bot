# Help

Discover the bot's available commands in Discord.

## Sub-features

- `/help` lists finance and shopping commands with option examples.
- Guild registration makes all eight slash commands discoverable.

## How to get to it (user POV)

Open the configured shopping channel and select the bot's `/help` from Discord's slash picker. The command has no channel restriction in its callback, but availability depends on guild registration and permissions.

## Driving it with Discord computer use

Run the skill's doctor, obtain a fresh accessibility snapshot, focus the channel message textbox, type `/help`, and select the expected bot's command. Capture the selection and submitted interaction. Submit and capture the response.

Pass when `Available Slash Commands:` appears with `/dindin`, `/detalhado`, `/sincronizar`, `/historico`, `/lista`, `/zerar`, `/ordenar`, and `/help`. Check that autocomplete offers those commands for this bot. Record action and reply timestamps and message references. This command reads no finance/shopping data and has no database write in its callback.

## Gotchas

- Plain text `/help` is not a slash-command invocation. Confirm the interaction rendering.
- There is no functioning `!help`; prefix-like text is ignored by the shopping handler.
- Stale guild commands can survive a broken new process. Require the doctor evidence for the target build.
