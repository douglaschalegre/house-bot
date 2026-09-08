from sqlalchemy import Identity, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ShoppingItemRecord(Base):
    __tablename__ = "shopping_items"
    __table_args__ = (Index("idx_shopping_items_list_id_id", "list_id", "id"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    list_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class ShoppingStateRecord(Base):
    __tablename__ = "shopping_state"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
