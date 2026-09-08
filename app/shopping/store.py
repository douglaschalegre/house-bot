from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import Database
from app.database.models.shopping import ShoppingItemRecord, ShoppingStateRecord
from app.domain.shopping import ShoppingList


CURRENT_LIST_ID_KEY = "current_list_id"


class ShoppingStore:
    def __init__(self, database: Database):
        self.database = database

    def _get_max_list_id(self, session: Session) -> int | None:
        return session.scalar(select(func.max(ShoppingItemRecord.list_id)))

    def _get_current_list_id(self, session: Session) -> int:
        state = session.get(ShoppingStateRecord, CURRENT_LIST_ID_KEY)
        if state is not None:
            return state.value

        list_id = self._get_max_list_id(session) or 1
        session.add(ShoppingStateRecord(key=CURRENT_LIST_ID_KEY, value=list_id))
        session.flush()
        return list_id

    def _list_items(self, session: Session, list_id: int) -> tuple[str, ...]:
        items = session.scalars(
            select(ShoppingItemRecord.content)
            .where(ShoppingItemRecord.list_id == list_id)
            .order_by(ShoppingItemRecord.id)
        ).all()
        return tuple(items)

    def add_items(self, items: Iterable[str]) -> int:
        cleaned_items = [item.strip() for item in items if item and item.strip()]

        with self.database.session() as session:
            list_id = self._get_current_list_id(session)
            session.add_all(
                ShoppingItemRecord(list_id=list_id, content=item)
                for item in cleaned_items
            )
            session.commit()
            return list_id

    def get_current_list_id(self) -> int:
        with self.database.session() as session:
            list_id = self._get_current_list_id(session)
            session.commit()
            return list_id

    def get_current_list(self) -> ShoppingList:
        with self.database.session() as session:
            list_id = self._get_current_list_id(session)
            items = self._list_items(session, list_id)
            session.commit()
            return ShoppingList(list_id=list_id, items=items)

    def list_current_items(self) -> list[str]:
        return list(self.get_current_list().items)

    def get_status(self) -> dict[str, int | str]:
        with self.database.session() as session:
            list_id = self._get_current_list_id(session)
            current_item_count = session.scalar(
                select(func.count(ShoppingItemRecord.id)).where(
                    ShoppingItemRecord.list_id == list_id
                )
            )
            max_list_id = self._get_max_list_id(session) or 0
            session.commit()
            return {
                "db_path": "postgresql",
                "current_list_id": list_id,
                "current_item_count": int(current_item_count or 0),
                "max_list_id": int(max_list_id),
            }

    def advance_list(self) -> int:
        with self.database.session() as session:
            list_id = self._get_current_list_id(session) + 1
            state = session.get(ShoppingStateRecord, CURRENT_LIST_ID_KEY)
            if state is None:
                raise RuntimeError("Shopping list state was not initialized")
            state.value = list_id
            session.commit()
            return list_id
