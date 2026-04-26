"""Date and academic-year parsing helpers shared by all scrapers."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, datetime

from dateutil import parser as dateparser  # type: ignore[import-untyped]

# Defaults need to be datetimes for dateutil's `default=` argument.
_DEFAULT_PIVOT = datetime(1900, 1, 1)

# Match a "<day> <month> [<year>]" or "<day>/<month>/<year>" date inside a longer
# string, optionally preceded by an ordinal suffix ("8th", "1st").
_DATE_IN_TEXT = re.compile(
    r"""
    (?P<day>\b\d{1,2})\s*(?:st|nd|rd|th)?
    \s*(?:of\s+)?
    (?P<month>
        Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
        Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|
        Nov(?:ember)?|Dec(?:ember)?
    )
    (?:\s*(?P<year>20\d{2}))?
    |
    (?P<day_n>\b\d{1,2})\s*[/-]\s*(?P<month_n>\d{1,2})\s*[/-]\s*(?P<year_n>20\d{2})
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


def parse_uk_date(text: str, default_year: int | None = None) -> date | None:
    """Parse a UK-style date string. Returns None if parsing fails.

    Examples accepted:
      "Monday 8 September 2025" -> 2025-09-08
      "8 September 2025"        -> 2025-09-08
      "8/9/2025"                -> 2025-09-08
      "Mon 27 October"  (with default_year=2025) -> 2025-10-27
    """
    text = text.strip().rstrip(".")
    if not text:
        return None

    # First pass: pull out the day/month/year directly. This avoids dateutil's
    # fuzzy mode mis-parsing weekday names ("Mon 27 October" -> 27 Jan).
    match = _DATE_IN_TEXT.search(text)
    if match is not None:
        if match.group("day"):
            day = int(match.group("day"))
            month = _MONTHS[match.group("month").lower()[:3]]
            year_str = match.group("year")
        else:
            day = int(match.group("day_n"))
            month = int(match.group("month_n"))
            year_str = match.group("year_n")
        year = int(year_str) if year_str else default_year
        if year is not None:
            try:
                return date(year, month, day)
            except ValueError:
                return None

    # Fallback: dateutil parser without fuzzy mode.
    try:
        default = (
            datetime(default_year, 1, 1) if default_year is not None else _DEFAULT_PIVOT
        )
        parsed = dateparser.parse(text, dayfirst=True, default=default)
    except (ValueError, OverflowError):
        return None
    if parsed is None:
        return None
    if isinstance(parsed, datetime):
        return parsed.date()
    if isinstance(parsed, date):
        return parsed
    return None


_MONTHS: dict[str, int] = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


_RANGE_SEP = re.compile(
    r"(?:\s+(?:to|until|through|and)\s+|\s*(?:–|—|-|&)\s*)",
    flags=re.IGNORECASE,
)


def parse_uk_date_range(text: str, default_year: int | None = None) -> tuple[date, date] | None:
    """Parse "Mon 8 Sep 2025 to Fri 12 Sep 2025" -> (2025-09-08, 2025-09-12).

    If the start side has no year, we infer it from the end side.
    """
    parts = _RANGE_SEP.split(text, maxsplit=1)
    if len(parts) != 2:
        return None
    end = parse_uk_date(parts[1], default_year=default_year)
    if end is None:
        return None
    start = parse_uk_date(parts[0], default_year=end.year)
    if start is None:
        return None
    # If start parsed to a year well after end, the start was missing a year and
    # picked up the wrong default — push it back a year.
    if start > end and start.year > end.year:
        start = start.replace(year=end.year)
        if start > end:
            start = start.replace(year=end.year - 1)
    return start, end


def expand_range(start: date, end: date, *, weekdays_only: bool = False) -> Iterable[date]:
    """Yield each date in the inclusive range start..end (optionally weekdays only)."""
    cur = start
    while cur <= end:
        if not weekdays_only or cur.weekday() < 5:
            yield cur
        cur = date.fromordinal(cur.toordinal() + 1)


def academic_year_for(d: date) -> str:
    """Return e.g. "2025/2026" for a date in or after September 2025.

    The English academic year boundary is 1 September.
    """
    if d.month >= 9:
        return f"{d.year}/{d.year + 1}"
    return f"{d.year - 1}/{d.year}"


def current_academic_year_start(today: date | None = None) -> int:
    """Return the September-start year of the academic year containing ``today``.

    On 2026-04-26 this returns 2025 (we are inside 2025/2026). Used as a sane
    default-year for parsers that may encounter yearless dates.
    """
    if today is None:
        from datetime import date as _date  # local to keep top-level import light
        today = _date.today()
    return today.year if today.month >= 9 else today.year - 1


# Match anywhere "INSET", "PD day", "Inset day", "Training day", "Staff training",
# "Professional Development", "Non-pupil day", "Occasional day".
PD_DAY_PATTERNS = re.compile(
    r"\b(INSET|PD day|professional development|training day|staff training|"
    r"non[- ]pupil day|occasional day|teacher training)\b",
    flags=re.IGNORECASE,
)


def looks_like_pd_day(label: str) -> bool:
    return bool(PD_DAY_PATTERNS.search(label))
