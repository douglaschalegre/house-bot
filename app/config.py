import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_token: str
    database_url: str
    openai_api_key: str
    credentials_path: Path
    dindin_url: str
    dindin_sync_token: str


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        dindin_url=_required_env("DINDIN_URL").rstrip("/"),
        dindin_sync_token=_required_env("DINDIN_SYNC_TOKEN"),
        discord_token=_required_env("DISCORD_TOKEN"),
        database_url=_required_env("DATABASE_URL"),
        openai_api_key=_required_env("OPENAI_API_KEY"),
        credentials_path=Path(
            os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        ),
    )


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value
