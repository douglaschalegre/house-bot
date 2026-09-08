from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


BRAZIL_TIMEZONE = timezone(timedelta(hours=-3))


@dataclass(frozen=True)
class FinancePeriod:
    month: str
    year: str

    @classmethod
    def current(cls) -> "FinancePeriod":
        now = datetime.now(BRAZIL_TIMEZONE)
        return cls(month=now.strftime("%m"), year=now.strftime("%y"))


@dataclass(frozen=True)
class FinanceEntry:
    period: FinancePeriod
    section: str
    source_cell: str
    value: str


@dataclass(frozen=True)
class FinanceSnapshot:
    period: FinancePeriod
    summary_rows: list[list[object]]
    detail_rows: list[list[object]]
    synced_at: str
