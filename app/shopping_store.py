import sqlite3
from pathlib import Path
from typing import Iterable


CURRENT_LIST_ID_KEY = "current_list_id"


class ShoppingStore:
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
                CREATE TABLE IF NOT EXISTS shopping_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    list_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS shopping_state (
                    key TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_shopping_items_list_id_id
                ON shopping_items (list_id, id)
                """
            )
            connection.execute(
                """
                INSERT OR IGNORE INTO shopping_state (key, value)
                VALUES (?, 1)
                """,
                (CURRENT_LIST_ID_KEY,),
            )

    def _get_current_list_id(self, connection) -> int:
        row = connection.execute(
            "SELECT value FROM shopping_state WHERE key = ?",
            (CURRENT_LIST_ID_KEY,),
        ).fetchone()

        if row is not None:
            return int(row[0])

        connection.execute(
            "INSERT INTO shopping_state (key, value) VALUES (?, 1)",
            (CURRENT_LIST_ID_KEY,),
        )
        return 1

    def add_items(self, items: Iterable[str]) -> int:
        cleaned_items = [item.strip() for item in items if item and item.strip()]

        with self._connect() as connection:
            list_id = self._get_current_list_id(connection)
            if cleaned_items:
                connection.executemany(
                    "INSERT INTO shopping_items (list_id, content) VALUES (?, ?)",
                    [(list_id, item) for item in cleaned_items],
                )
            return list_id

    def get_current_list_id(self) -> int:
        with self._connect() as connection:
            return self._get_current_list_id(connection)

    def list_current_items(self) -> list[str]:
        with self._connect() as connection:
            list_id = self._get_current_list_id(connection)
            rows = connection.execute(
                """
                SELECT content
                FROM shopping_items
                WHERE list_id = ?
                ORDER BY id
                """,
                (list_id,),
            ).fetchall()
            return [row[0] for row in rows]

    def advance_list(self) -> int:
        with self._connect() as connection:
            list_id = self._get_current_list_id(connection) + 1
            connection.execute(
                "UPDATE shopping_state SET value = ? WHERE key = ?",
                (list_id, CURRENT_LIST_ID_KEY),
            )
            return list_id
