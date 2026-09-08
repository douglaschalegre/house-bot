# house-bot

Discord bot to help manage house management data.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker Engine + Docker Compose plugin

## Local Development with uv

1. Create `.env` from `.env-example` and fill values:
   - `DISCORD_TOKEN`
   - `OPENAI_API_KEY`
   - `DATABASE_URL`
2. Place `credentials.json` at the repository root.
3. Install dependencies:

```bash
uv sync
```

4. Run bot:

```bash
uv run python main.py
```

Financial imports are owned by Dindin. The `/sincronizar` command requests
an import from Dindin and confirms success only after the database transaction
commits. On a timeout, completion is unconfirmed; inspect the last sync timestamp
before retrying. Dindin imports the current month at startup and hourly.

Configure these environment variables alongside the existing Discord and Google settings:

- `DATABASE_URL`: the existing PostgreSQL connection, shared with Dindin.
- `DINDIN_URL`: Dindin's private Tailscale HTTPS origin (no `/api` suffix).
- `DINDIN_SYNC_TOKEN`: the service token configured as `DINDIN_FINANCE_SYNC_TOKEN` in Dindin.

Dindin's `docs/finance-import-cutover.md` describes cutover and rollback. The bot no longer
creates or writes financial tables. Its monthly report still reads the summary
from Google Sheets, so Google credentials remain required.

## Docker Compose

After pulling new commits on the server, rebuild and recreate the container:

```bash
cd ~/house-bot
git pull
sudo docker compose up -d --build --force-recreate
```

Tail logs:

```bash
sudo docker compose logs -f house-bot
```

Restart without code changes:

```bash
sudo docker compose restart house-bot
```

Stop:

```bash
sudo docker compose down
```

## Cutover from systemd

Replace `house-bot.service` with your actual unit name if different.

1. Stop/disable old host process:

```bash
sudo systemctl stop house-bot.service
sudo systemctl disable house-bot.service
```

2. Start Docker service:

```bash
sudo docker compose up -d --build --force-recreate
sudo docker compose logs -f house-bot
```

3. Validate in Discord (`/help` or `/lista`) before considering cutover complete.

## Rollback to systemd

1. Stop Docker service:

```bash
sudo docker compose down
```

2. Re-enable previous systemd unit:

```bash
sudo systemctl enable --now house-bot.service
```
