from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Protocol, Sequence

import gspread

if TYPE_CHECKING:
    from app.finance.store import FinanceStore

from app.domain.finance import BRAZIL_TIMEZONE, FinanceEntry, FinancePeriod


logger = logging.getLogger(__name__)

FINANCE_RANGES = {
    "summary": ("M6:O8", "M6"),
    "detail": ("M10:O22", "M10"),
    "monthly_expenses": ("A27:E115", "A27"),
    "fixed_expenses": ("H17:K31", "H17"),
    "installments": ("H35:K47", "H35"),
    "subscriptions": ("H85:K97", "H85"),
}


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

    def read(self, period: FinancePeriod) -> dict[str, list[list[object]]]:
        sheet = self._get_sheet(period)
        return {
            section: sheet.sheet1.get(range_name)
            for section, (range_name, _) in FINANCE_RANGES.items()
        }

    def read_summary(self, period: FinancePeriod) -> list[list[object]]:
        return self._get_sheet(period).sheet1.get(FINANCE_RANGES["summary"][0])

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

    def synchronize(self, period: FinancePeriod) -> str:
        values = self.sheet_reader.read(period)
        entries = [
            entry
            for section, (_, start_cell) in FINANCE_RANGES.items()
            for entry in annotate_cells(period, section, values[section], start_cell)
        ]
        return self.store.save_snapshot(
            period,
            values["summary"],
            values["detail"],
            entries,
        )

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


def column_name(column_number: int) -> str:
    if column_number < 1:
        raise ValueError("Column numbers start at 1")

    name = ""
    while column_number:
        column_number, remainder = divmod(column_number - 1, 26)
        name = chr(65 + remainder) + name
    return name


def annotate_cells(
    period: FinancePeriod,
    section: str,
    values: Sequence[Sequence[object]],
    start_cell: str,
) -> list[FinanceEntry]:
    match = re.fullmatch(r"([A-Z]+)([0-9]+)", start_cell)
    if match is None:
        raise ValueError(f"Invalid start cell: {start_cell}")

    start_column = 0
    for character in match.group(1):
        start_column = start_column * 26 + ord(character) - ord("A") + 1
    start_row = int(match.group(2))

    return [
        FinanceEntry(
            period=period,
            section=section,
            source_cell=f"{column_name(start_column + column_index)}{start_row + row_index}",
            value="" if value is None else str(value),
        )
        for row_index, row in enumerate(values)
        for column_index, value in enumerate(row)
    ]


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
