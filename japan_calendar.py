"""Japanese business-day calendar: weekdays excluding national holidays."""

from __future__ import annotations

import calendar
from datetime import date
from functools import lru_cache

import holidays


@lru_cache(maxsize=1)
def japan_holidays(start_year: int, end_year: int) -> frozenset[date]:
    """National holidays of Japan, including 振替休日 and 国民の休日."""
    jp = holidays.country_holidays("JP", years=range(start_year, end_year + 1))
    return frozenset(jp.keys())


def is_business_day(d: date, holiday_set: frozenset[date]) -> bool:
    return d.weekday() < 5 and d not in holiday_set


def is_company_shutdown(d: date) -> bool:
    """Company is closed 29 Dec–3 Jan every year, any day of week."""
    return (d.month == 12 and d.day >= 29) or (d.month == 1 and d.day <= 3)


def is_company_business_day(d: date, holiday_set: frozenset[date]) -> bool:
    return is_business_day(d, holiday_set) and not is_company_shutdown(d)


def business_days_in_month(
    year: int, month: int, holiday_set: frozenset[date]
) -> list[date]:
    _, last = calendar.monthrange(year, month)
    return [
        date(year, month, day)
        for day in range(1, last + 1)
        if is_business_day(date(year, month, day), holiday_set)
    ]


def company_business_days_in_month(
    year: int, month: int, holiday_set: frozenset[date]
) -> list[date]:
    _, last = calendar.monthrange(year, month)
    return [
        date(year, month, day)
        for day in range(1, last + 1)
        if is_company_business_day(date(year, month, day), holiday_set)
    ]


def month_range(start: date, end: date) -> list[tuple[int, int]]:
    """Inclusive list of (year, month) from start's month through end's month."""
    months: list[tuple[int, int]] = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        months.append((y, m))
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return months
