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

After starting the bot, synchronize the current finance period once with
`/sincronizar`. Finance commands then read the local PostgreSQL snapshot.

The bot also synchronizes the current finance period when it starts and every
hour afterward. Other periods can be synchronized with `/sincronizar` using
the month and year options.

The synchronization reads `M6:O8`, `M10:O22`, `A27:E115`, `H17:K31`,
`H35:K47`, and `H85:K97`. Every extracted cell is also stored in the
`finance_entries` table with its section, source cell, and value.

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
