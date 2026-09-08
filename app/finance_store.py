import json
from datetime import datetime, timezone

import psycopg


class FinanceStore:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._initialize()

    def _connect(self):
        return psycopg.connect(self.database_url)

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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS finance_entries (
                    month TEXT NOT NULL,
                    year TEXT NOT NULL,
                    section TEXT NOT NULL,
                    source_cell TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (month, year, section, source_cell)
                )
                """
            )

    def save_snapshot(
        self,
        month: str,
        year: str,
        summary_rows: list[list[str]],
        detail_rows: list[list[str]],
        entries: list[tuple[str, str, str]],
    ) -> str:
        synced_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO finance_snapshots
                    (month, year, summary_rows, detail_rows, synced_at)
                VALUES (%s, %s, %s, %s, %s)
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
            connection.execute(
                "DELETE FROM finance_entries WHERE month = %s AND year = %s",
                (month, year),
            )
            connection.executemany(
                """
                INSERT INTO finance_entries
                    (month, year, section, source_cell, value)
                VALUES (%s, %s, %s, %s, %s)
                """,
                [(month, year, section, source_cell, value) for section, source_cell, value in entries],
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
                WHERE month = %s AND year = %s
                """,
                (month, year),
            ).fetchone()

        if row is None:
            return None
        return json.loads(row[0]), json.loads(row[1]), row[2]

    def get_entries(self, month: str, year: str) -> list[tuple[str, str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT section, source_cell, value
                FROM finance_entries
                WHERE month = %s AND year = %s
                ORDER BY section, source_cell
                """,
                (month, year),
            ).fetchall()
        return [(row[0], row[1], row[2]) for row in rows]
