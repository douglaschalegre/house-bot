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
2. Place `credentials.json` at the repository root.
3. Install dependencies:

```bash
uv sync
```

4. Run bot:

```bash
uv run python main.py
```

## Run with Docker Compose

1. Ensure `.env` and `credentials.json` exist in the repository root.
2. Build and start:

```bash
docker compose up -d --build
```

3. Tail logs:

```bash
docker compose logs -f house-bot
```

4. Restart:

```bash
docker compose restart house-bot
```

5. Stop:

```bash
docker compose down
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
docker compose up -d --build
docker compose logs -f house-bot
```

3. Validate in Discord (`/help` or `/lista`) before considering cutover complete.

## Rollback to systemd

1. Stop Docker service:

```bash
docker compose down
```

2. Re-enable previous systemd unit:

```bash
sudo systemctl enable --now house-bot.service
```
