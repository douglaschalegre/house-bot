from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FinanceSnapshotRecord(Base):
    __tablename__ = "finance_snapshots"

    month: Mapped[str] = mapped_column(Text, primary_key=True)
    year: Mapped[str] = mapped_column(Text, primary_key=True)
    summary_rows: Mapped[str] = mapped_column(Text, nullable=False)
    detail_rows: Mapped[str] = mapped_column(Text, nullable=False)
    synced_at: Mapped[str] = mapped_column(Text, nullable=False)


class FinanceEntryRecord(Base):
    __tablename__ = "finance_entries"

    month: Mapped[str] = mapped_column(Text, primary_key=True)
    year: Mapped[str] = mapped_column(Text, primary_key=True)
    section: Mapped[str] = mapped_column(Text, primary_key=True)
    source_cell: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
