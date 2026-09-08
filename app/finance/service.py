from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Protocol, Sequence

import gspread

if TYPE_CHECKING:
    from app.finance.store import FinanceStore

from app.domain.finance import BRAZIL_TIMEZONE, FinancePeriod


logger = logging.getLogger(__name__)

class Worksheet(Protocol):
    def get(self, range_name: str) -> list[list[object]]: ...


class SheetsClient(Protocol):
    def open(self, title: str) -> Spreadsheet: ...


class Spreadsheet(Protocol):
    sheet1: Worksheet


class FinanceSheetNotFound(RuntimeError):
    pass


class FinanceSheetReader:
    def __init__(self, client: SheetsClient):
        self.client = client

    def read_summary(self, period: FinancePeriod) -> list[list[object]]:
        return self._get_sheet(period).sheet1.get("M6:O8")

    def _get_sheet(self, period: FinancePeriod) -> Spreadsheet:
        title = f"Expenses {period.month}/{period.year}"
        try:
            return self.client.open(title)
        except gspread.exceptions.SpreadsheetNotFound as error:
            raise FinanceSheetNotFound(title) from error


class FinanceService:
    def __init__(self, store: FinanceStore, sheet_reader: FinanceSheetReader):
        self.store = store
        self.sheet_reader = sheet_reader

    def response(self, period: FinancePeriod, detailed: bool = False) -> str:
        snapshot = self.store.get_snapshot(period)
        if snapshot is None:
            return (
                "Finance data is not synchronized for this period. "
                "Run `/sincronizar` first."
            )

        summary_values = snapshot.summary_rows
        detail_values = snapshot.detail_rows
        if detailed:
            table = format_detailed_expenses(summary_values, detail_values, period)
        else:
            table = format_finance_summary(summary_values, period)
        return (
            f"```\n{table}\n```\n"
            f"_Última sincronização: {format_sync_time(snapshot.synced_at)}_"
        )

    def current_summary(self, period: FinancePeriod) -> str:
        return format_finance_summary(self.sheet_reader.read_summary(period), period)


def normalize_row(
    row: Sequence[object], width: int = 3, fill: str = "-"
) -> list[str]:
    normalized = []
    for index in range(width):
        value = row[index] if index < len(row) else ""
        value = "" if value is None else str(value).strip()
        normalized.append(value if value else fill)
    return normalized


def is_effectively_empty_row(row: Sequence[object]) -> bool:
    return not row or all(cell is None or not str(cell).strip() for cell in row)


def format_finance_summary(
    values: Sequence[Sequence[object]], period: FinancePeriod
) -> str:
    data = []
    for offset, name in enumerate(("Douglas", "Luana", "Total"), start=1):
        row = values[offset - 1] if offset - 1 < len(values) else []
        if len(row) < 3 or any(
            cell is None or not str(cell).strip() for cell in row[:3]
        ):
            logger.warning("Partial finance summary row at offset %s: %s", offset, row)
        data.append((name, *normalize_row(row)))

    lines = [
        f"Sheet: Expenses {period.month}/{period.year}",
        f"{'Name':<10} {'Salary':<10} {'Percent':<10} {'Contribution':<15}",
        "-" * 45,
    ]
    lines.extend(
        f"{name:<10} {salary:<10} {percent:<10} {contribution:<15}"
        for name, salary, percent, contribution in data
    )
    return "\n".join(lines) + "\n"


def format_detailed_expenses(
    summary_values: Sequence[Sequence[object]],
    detail_values: Sequence[Sequence[object]],
    period: FinancePeriod,
) -> str:
    lines = [format_finance_summary(summary_values, period).rstrip("\n"), "-" * 45]
    for offset, row in enumerate(detail_values, start=1):
        if is_effectively_empty_row(row):
            continue
        if len(row) < 3 or any(
            cell is None or not str(cell).strip() for cell in row[:3]
        ):
            logger.warning("Partial finance detail row at offset %s: %s", offset, row)
        name, value, value_type = normalize_row(row)
        lines.append(f"{name:<20} {value:<10} {value_type:<15}")
    return "\n".join(lines) + "\n"


def format_sync_time(synced_at: str) -> str:
    timestamp = datetime.fromisoformat(synced_at)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(BRAZIL_TIMEZONE).strftime("%d/%m/%Y %H:%M:%S")
