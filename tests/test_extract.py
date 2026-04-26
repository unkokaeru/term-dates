"""Tests for the generic PD-day extractor in term_dates.schools._extract.

These cover the harder-to-eyeball behaviours that the live data exposed:

* a PD-keyword line followed by bare-date sibling lines (PDF wrapping)
* lonely "<weekday> <day>" tokens that must inherit a sibling's month/year
* spillover that closes when a different label appears
"""

from __future__ import annotations

from datetime import date

from term_dates.parsing import current_academic_year_start
from term_dates.schools._extract import extract_pd_days


def test_spillover_picks_up_sibling_dates_after_keyword_line() -> None:
    """Carlton-style PDF: keyword on one line, dates wrapped onto the next."""
    text = (
        "Autumn Term 1 (38 Days) Dates\n"
        "Inset days (school closed to pupils) Monday, 1 September 2025\n"
        "Tuesday, 2 September 2025\n"
        "First day in school for pupils Wednesday, 3 September 2025\n"
    )
    days = extract_pd_days(text)
    dates = {d.date for d in days}
    assert date(2025, 9, 1) in dates
    assert date(2025, 9, 2) in dates  # spillover sibling
    assert date(2025, 9, 3) not in dates  # different label closes the window


def test_spillover_closes_on_different_label() -> None:
    """A subsequent dated line that starts with non-date text must NOT bleed in."""
    text = (
        "INSET Day (School closed to\n"
        "pupils)\n"
        "Monday 4th January 2027\n"
        "First day in school for pupils Tuesday 5th January 2027\n"
    )
    days = extract_pd_days(text)
    dates = {d.date for d in days}
    assert date(2027, 1, 4) in dates
    assert date(2027, 1, 5) not in dates


def test_spillover_blank_line_closes_window() -> None:
    text = (
        "Inset day\n"
        "\n"
        "Monday 13 February 2026\n"
    )
    days = extract_pd_days(text)
    assert days == ()


def test_lonely_day_inherits_month_from_sibling() -> None:
    """Priory-style: 'Thursday 3 rd and Friday 4 th September 2026' = two PDs."""
    text = (
        "Staff training days | Thursday 3 rd and Friday 4 th September 2026 "
        "Monday 4 th January 2027\n"
    )
    days = extract_pd_days(text)
    dates = {d.date for d in days}
    assert date(2026, 9, 3) in dates
    assert date(2026, 9, 4) in dates
    assert date(2027, 1, 4) in dates


def test_yearless_day_inherits_year_from_later_sibling() -> None:
    """A date with no year picks up the year from the next dated sibling."""
    text = "INSET: 27 March and 30 March 2027\n"
    days = extract_pd_days(text)
    dates = {d.date for d in days}
    assert date(2027, 3, 27) in dates
    assert date(2027, 3, 30) in dates


def test_label_carries_source_label_prefix() -> None:
    text = "INSET Day: Monday 1 September 2025\n"
    days = extract_pd_days(text, source_label="My School")
    assert days[0].label.startswith("My School:")


def test_current_academic_year_start_in_april() -> None:
    """26 April 2026 sits inside the 2025/2026 academic year."""
    assert current_academic_year_start(date(2026, 4, 26)) == 2025


def test_current_academic_year_start_in_september() -> None:
    assert current_academic_year_start(date(2025, 9, 1)) == 2025
    assert current_academic_year_start(date(2025, 8, 31)) == 2024
