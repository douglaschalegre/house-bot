from __future__ import annotations

import json

from sqlalchemy import select

from app.database import Database
from app.database.models.finance import FinanceEntryRecord, FinanceSnapshotRecord
from app.domain.finance import FinanceEntry, FinancePeriod, FinanceSnapshot


class FinanceStore:
    def __init__(self, database: Database):
        self.database = database

    def get_snapshot(self, period: FinancePeriod) -> FinanceSnapshot | None:
        with self.database.session() as session:
            record = session.get(
                FinanceSnapshotRecord, (period.month, period.year)
            )

        if record is None:
            return None
        return FinanceSnapshot(
            period=period,
            summary_rows=json.loads(record.summary_rows),
            detail_rows=json.loads(record.detail_rows),
            synced_at=record.synced_at,
        )

    def get_entries(self, period: FinancePeriod) -> list[FinanceEntry]:
        with self.database.session() as session:
            records = session.scalars(
                select(FinanceEntryRecord)
                .where(
                    FinanceEntryRecord.month == period.month,
                    FinanceEntryRecord.year == period.year,
                )
                .order_by(
                    FinanceEntryRecord.section,
                    FinanceEntryRecord.source_cell,
                )
            ).all()

        return [
            FinanceEntry(
                period=period,
                section=record.section,
                source_cell=record.source_cell,
                value=record.value,
            )
            for record in records
        ]
