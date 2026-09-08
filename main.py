import logging

from app.bot import create_bot
from app.config import load_settings


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    create_bot(settings).run(settings.discord_token)


if __name__ == "__main__":
    main()
