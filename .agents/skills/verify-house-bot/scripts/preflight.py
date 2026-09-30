#!/usr/bin/env python3
"""Read-only local prerequisites; prints names and booleans, never credentials."""
import importlib.metadata
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from dotenv import dotenv_values


def main():
    values = {**dotenv_values(ROOT / ".env"), **os.environ}
    required = (
        "DISCORD_TOKEN", "DATABASE_URL", "OPENAI_API_KEY",
        "DINDIN_URL", "DINDIN_SYNC_TOKEN",
    )
    missing = [name for name in required if not values.get(name)]
    credentials = Path(values.get("GOOGLE_CREDENTIALS_PATH") or "credentials.json")
    if not credentials.is_absolute():
        credentials = ROOT / credentials
    valid_credentials = False
    try:
        data = json.loads(credentials.read_text())
        valid_credentials = all(data.get(key) for key in (
            "client_email", "private_key", "token_uri",
        ))
    except (OSError, ValueError):
        pass
    packages = {}
    for name in ("discord.py", "SQLAlchemy", "psycopg", "gspread", "openai", "APScheduler"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    ready = (
        sys.version_info[:2] == (3, 12) and not missing
        and valid_credentials and all(packages.values())
    )
    print(json.dumps({
        "local_prerequisites_ok": ready,
        "python": ".".join(map(str, sys.version_info[:3])),
        "missing_settings": missing,
        "google_credentials_shape_ok": valid_credentials,
        "packages": packages,
        "network_requests": 0,
        "live_auth_checked": False,
        "note": "This check does not establish Discord readiness or exclusive ownership.",
    }, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
