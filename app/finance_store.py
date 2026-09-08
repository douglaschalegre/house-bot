import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class FinanceStore:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS finance_snapshots (
                    month TEXT NOT NULL,
                    year TEXT NOT NULL,
                    summary_rows TEXT NOT NULL,
                    detail_rows TEXT NOT NULL,
                    synced_at TEXT NOT NULL,
                    PRIMARY KEY (month, year)
                )
                """
            )

    def save_snapshot(
        self,
        month: str,
        year: str,
        summary_rows: list[list[str]],
        detail_rows: list[list[str]],
    ) -> str:
        synced_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO finance_snapshots
                    (month, year, summary_rows, detail_rows, synced_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(month, year) DO UPDATE SET
                    summary_rows = excluded.summary_rows,
                    detail_rows = excluded.detail_rows,
                    synced_at = excluded.synced_at
                """,
                (
                    month,
                    year,
                    json.dumps(summary_rows),
                    json.dumps(detail_rows),
                    synced_at,
                ),
            )
        return synced_at

    def get_snapshot(
        self, month: str, year: str
    ) -> tuple[list[list[str]], list[list[str]], str] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT summary_rows, detail_rows, synced_at
                FROM finance_snapshots
                WHERE month = ? AND year = ?
                """,
                (month, year),
            ).fetchone()

        if row is None:
            return None
        return json.loads(row[0]), json.loads(row[1]), row[2]
