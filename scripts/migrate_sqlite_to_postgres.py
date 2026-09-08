import os
import sqlite3
from pathlib import Path

import psycopg

from app.finance_store import FinanceStore
from app.shopping_store import ShoppingStore


SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/shopping_list.sqlite3")
DATABASE_URL = os.getenv("DATABASE_URL")


def sqlite_table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        is not None
    )


def migrate(sqlite_db_path: str, database_url: str) -> None:
    sqlite_path = Path(sqlite_db_path)
    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")

    # These constructors create the target schema without modifying the source.
    ShoppingStore(database_url)
    FinanceStore(database_url)

    with sqlite3.connect(sqlite_path) as source, psycopg.connect(database_url) as target:
        target_counts = target.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM shopping_items),
                (SELECT COUNT(*) FROM finance_snapshots),
                (SELECT COUNT(*) FROM finance_entries)
            """
        ).fetchone()
        if any(target_counts):
            raise RuntimeError(
                "Target database is not empty; refusing to duplicate migrated data."
            )

        shopping_items = source.execute(
            "SELECT id, list_id, content, created_at FROM shopping_items ORDER BY id"
        ).fetchall()
        target.executemany(
            """
            INSERT INTO shopping_items (id, list_id, content, created_at)
            VALUES (%s, %s, %s, %s)
            """,
            shopping_items,
        )
        target.execute(
            """
            SELECT setval(
                pg_get_serial_sequence('shopping_items', 'id'),
                COALESCE(MAX(id), 1),
                MAX(id) IS NOT NULL
            )
            FROM shopping_items
            """
        )

        shopping_state = source.execute(
            "SELECT key, value FROM shopping_state"
        ).fetchall()
        target.executemany(
            """
            INSERT INTO shopping_state (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            shopping_state,
        )

        if sqlite_table_exists(source, "finance_snapshots"):
            target.executemany(
                """
                INSERT INTO finance_snapshots
                    (month, year, summary_rows, detail_rows, synced_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                source.execute(
                    """
                    SELECT month, year, summary_rows, detail_rows, synced_at
                    FROM finance_snapshots
                    """
                ).fetchall(),
            )

        if sqlite_table_exists(source, "finance_entries"):
            target.executemany(
                """
                INSERT INTO finance_entries
                    (month, year, section, source_cell, value)
                VALUES (%s, %s, %s, %s, %s)
                """,
                source.execute(
                    """
                    SELECT month, year, section, source_cell, value
                    FROM finance_entries
                    """
                ).fetchall(),
            )


if __name__ == "__main__":
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required")
    migrate(SQLITE_DB_PATH, DATABASE_URL)
    print("SQLite data migrated to PostgreSQL successfully.")
