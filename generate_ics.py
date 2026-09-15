"""Build a Google Calendar .ics of company Nth-business-day reminders."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from pathlib import Path

from japan_calendar import (
    company_business_days_in_month,
    japan_holidays,
    month_range,
)

TZID = "Asia/Tokyo"
PRODID = "-//date_variation//company-business-days//EN"
UID_DOMAIN = "date-variation.local"

# Next 10 years of complete months from this project's "today".
DEFAULT_START = date(2026, 9, 1)
DEFAULT_END = date(2036, 8, 31)

CALENDARS = {
    "timesheet": {
        "cal_name": "Company business-day reminders",
        "output": Path(__file__).with_name("reminders.ics"),
        "events": (
            {
                "kind": "timesheet",
                "n": 1,
                "hour": 9,
                "summary": "Fill timesheet and file invoices",
                "description": "First company business day of the month.",
            },
            {
                "kind": "deadline-am",
                "n": 3,
                "hour": 9,
                "summary": "Deadline: approve timesheets and invoices",
                "description": "Third company business day of the month (morning).",
            },
            {
                "kind": "deadline-pm",
                "n": 3,
                "hour": 17,
                "summary": "Deadline: approve timesheets and invoices",
                "description": "Third company business day of the month (evening).",
            },
        ),
    },
    "oncall": {
        "cal_name": "On-call pay reminders",
        "output": Path(__file__).with_name("oncall_pay.ics"),
        "events": (
            {
                "kind": "oncall-generate",
                "n": 2,
                "hour": 9,
                "summary": "Generate on-call pay and share it with HR",
                "description": "Second company business day of the month.",
            },
            {
                "kind": "oncall-share",
                "n": 4,
                "hour": 9,
                "summary": "Generate on-call pay and share it with HR",
                "description": "Fourth company business day of the month.",
            },
        ),
    },
}


def nth_company_business_day(
    year: int, month: int, n: int, holiday_set: frozenset[date]
) -> date:
    days = company_business_days_in_month(year, month, holiday_set)
    if n < 1 or n > len(days):
        raise ValueError(f"{year}-{month:02d} has {len(days)} company business days; need N={n}")
    return days[n - 1]


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    if len(line) <= 75:
        return line
    parts = [line[:75]]
    rest = line[75:]
    while rest:
        parts.append(" " + rest[:74])
        rest = rest[74:]
    return "\r\n".join(parts)


def _vevent(
    *,
    kind: str,
    day: date,
    hour: int,
    summary: str,
    description: str,
    dtstamp: str,
) -> list[str]:
    start = f"{day:%Y%m%d}T{hour:02d}0000"
    end_hour = hour
    end_min = 30
    uid = f"{kind}-{day:%Y-%m}@{UID_DOMAIN}"
    return [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;TZID={TZID}:{start}",
        f"DTEND;TZID={TZID}:{day:%Y%m%d}T{end_hour:02d}{end_min:02d}00",
        f"SUMMARY:{_escape(summary)}",
        f"DESCRIPTION:{_escape(description)}",
        "STATUS:CONFIRMED",
        "TRANSP:TRANSPARENT",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"DESCRIPTION:{_escape(summary)}",
        "TRIGGER:PT0S",
        "END:VALARM",
        "END:VEVENT",
    ]


def build_ics(
    start: date = DEFAULT_START,
    end: date = DEFAULT_END,
    dtstamp: datetime | None = None,
    calendar: str = "timesheet",
) -> str:
    if calendar not in CALENDARS:
        raise ValueError(f"unknown calendar: {calendar}")
    spec = CALENDARS[calendar]
    stamp = (dtstamp or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    holiday_set = japan_holidays(start.year, end.year)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(spec['cal_name'])}",
        f"X-WR-TIMEZONE:{TZID}",
        "BEGIN:VTIMEZONE",
        f"TZID:{TZID}",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:+0900",
        "TZOFFSETTO:+0900",
        "TZNAME:JST",
        "DTSTART:19700101T000000",
        "END:STANDARD",
        "END:VTIMEZONE",
    ]
    for year, month in month_range(start, end):
        for event in spec["events"]:
            day = nth_company_business_day(year, month, event["n"], holiday_set)
            lines.extend(
                _vevent(
                    kind=event["kind"],
                    day=day,
                    hour=event["hour"],
                    summary=event["summary"],
                    description=event["description"],
                    dtstamp=stamp,
                )
            )
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Write an .ics of company business-day reminders (Japan + 12/29–1/3 shutdown)."
    )
    parser.add_argument(
        "--calendar",
        choices=sorted(CALENDARS),
        default="timesheet",
        help="Which reminder set to write (default: timesheet).",
    )
    parser.add_argument("--start", type=date.fromisoformat, default=DEFAULT_START)
    parser.add_argument("--end", type=date.fromisoformat, default=DEFAULT_END)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    calendar = CALENDARS[args.calendar]
    output = args.output or calendar["output"]
    ics = build_ics(args.start, args.end, calendar=args.calendar)
    output.write_bytes(ics.encode("utf-8"))
    months = len(month_range(args.start, args.end))
    print(f"Wrote {output} ({months} months, {months * len(calendar['events'])} events)")


if __name__ == "__main__":
    main()
