from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import delete, select

from app.database import Database
from app.database.models.finance import FinanceEntryRecord, FinanceSnapshotRecord
from app.domain.finance import FinanceEntry, FinancePeriod, FinanceSnapshot


class FinanceStore:
    def __init__(self, database: Database):
        self.database = database

    def save_snapshot(
        self,
        period: FinancePeriod,
        summary_rows: list[list[object]],
        detail_rows: list[list[object]],
        entries: list[FinanceEntry],
    ) -> str:
        synced_at = datetime.now(timezone.utc).isoformat()
        with self.database.session() as session:
            snapshot = session.get(
                FinanceSnapshotRecord, (period.month, period.year)
            )
            if snapshot is None:
                snapshot = FinanceSnapshotRecord(
                    month=period.month,
                    year=period.year,
                )
                session.add(snapshot)

            snapshot.summary_rows = json.dumps(summary_rows)
            snapshot.detail_rows = json.dumps(detail_rows)
            snapshot.synced_at = synced_at

            session.execute(
                delete(FinanceEntryRecord).where(
                    FinanceEntryRecord.month == period.month,
                    FinanceEntryRecord.year == period.year,
                )
            )
            session.add_all(
                FinanceEntryRecord(
                    month=entry.period.month,
                    year=entry.period.year,
                    section=entry.section,
                    source_cell=entry.source_cell,
                    value=entry.value,
                )
                for entry in entries
            )
            session.commit()
        return synced_at

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
