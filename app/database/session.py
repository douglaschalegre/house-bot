from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.base import Base


class Database:
    def __init__(self, database_url: str, *, create_shopping_tables: bool = True):
        self.engine = create_engine(_sqlalchemy_url(database_url))
        if create_shopping_tables:
            from app.database.models.shopping import (
                ShoppingItemRecord,
                ShoppingStateRecord,
            )

            Base.metadata.create_all(
                self.engine,
                tables=[ShoppingStateRecord.__table__, ShoppingItemRecord.__table__],
            )
        self._session_factory = sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
        )

    @contextmanager
    def session(self) -> Iterator[Session]:
        with self._session_factory() as session:
            yield session


def _sqlalchemy_url(database_url: str) -> str:
    for prefix in ("postgresql://", "postgres://"):
        if database_url.startswith(prefix):
            return "postgresql+psycopg://" + database_url[len(prefix) :]
    return database_url
