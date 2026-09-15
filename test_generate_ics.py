from datetime import date, datetime, timezone

from generate_ics import build_ics, nth_company_business_day
from japan_calendar import (
    company_business_days_in_month,
    is_company_business_day,
    is_company_shutdown,
    japan_holidays,
)


def test_shutdown_covers_weekdays_and_weekends():
    assert is_company_shutdown(date(2026, 12, 29))
    assert is_company_shutdown(date(2027, 1, 1))
    assert is_company_shutdown(date(2027, 1, 3))
    assert not is_company_shutdown(date(2026, 12, 28))
    assert not is_company_shutdown(date(2027, 1, 4))


def test_company_skips_jan_2_even_when_not_a_national_holiday():
    holidays = japan_holidays(2026, 2026)
    # 2026-01-02 is Friday and not a national holiday.
    assert date(2026, 1, 2).weekday() == 4
    assert date(2026, 1, 2) not in holidays
    assert not is_company_business_day(date(2026, 1, 2), holidays)


def test_january_2026_starts_on_the_5th():
    holidays = japan_holidays(2026, 2026)
    days = company_business_days_in_month(2026, 1, holidays)
    assert days[0] == date(2026, 1, 5)
    assert days[2] == date(2026, 1, 7)


def test_january_2029_third_day_skips_coming_of_age_day():
    holidays = japan_holidays(2029, 2029)
    assert nth_company_business_day(2029, 1, 1, holidays) == date(2029, 1, 4)
    assert nth_company_business_day(2029, 1, 3, holidays) == date(2029, 1, 9)


def test_december_first_and_third_ignore_year_end_shutdown():
    holidays = japan_holidays(2026, 2026)
    days = company_business_days_in_month(2026, 12, holidays)
    assert days[0] == date(2026, 12, 1)
    assert days[2] == date(2026, 12, 3)
    assert date(2026, 12, 29) not in days
    assert date(2026, 12, 30) not in days
    assert date(2026, 12, 31) not in days


def test_january_2029_second_and_fourth_company_days():
    holidays = japan_holidays(2029, 2029)
    assert nth_company_business_day(2029, 1, 2, holidays) == date(2029, 1, 5)
    assert nth_company_business_day(2029, 1, 4, holidays) == date(2029, 1, 10)


def test_ics_has_three_timed_events_for_a_known_month():
    ics = build_ics(
        date(2029, 1, 1),
        date(2029, 1, 31),
        dtstamp=datetime(2026, 9, 12, tzinfo=timezone.utc),
    )
    assert ics.startswith("BEGIN:VCALENDAR")
    assert ics.count("BEGIN:VEVENT") == 3
    assert "DTSTART;TZID=Asia/Tokyo:20290104T090000" in ics
    assert "DTSTART;TZID=Asia/Tokyo:20290109T090000" in ics
    assert "DTSTART;TZID=Asia/Tokyo:20290109T170000" in ics
    assert "UID:timesheet-2029-01@date-variation.local" in ics
    assert "Fill timesheet and file invoices" in ics


def test_oncall_ics_has_second_and_fourth_day_events():
    ics = build_ics(
        date(2029, 1, 1),
        date(2029, 1, 31),
        dtstamp=datetime(2026, 9, 12, tzinfo=timezone.utc),
        calendar="oncall",
    )
    assert "X-WR-CALNAME:On-call pay reminders" in ics
    assert ics.count("BEGIN:VEVENT") == 2
    assert "DTSTART;TZID=Asia/Tokyo:20290105T090000" in ics
    assert "DTSTART;TZID=Asia/Tokyo:20290110T090000" in ics
    assert "Generate on-call pay and share it with HR" in ics
