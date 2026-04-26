"""Test the Lincolnshire LEA term-dates parser against a fixture HTML page.

The fixture mirrors the live page layout: ``<h3>`` headings per school year
and per-season tables with rows ``Term 1 / Half term / Christmas holiday`` etc.
"""

from __future__ import annotations

from datetime import date

from term_dates.lea.lincolnshire import LincolnshireProvider
from term_dates.models import EventKind


def test_parses_two_academic_years(lincolnshire_html: str) -> None:
    provider = LincolnshireProvider()
    td = provider.parse(lincolnshire_html, source_url="https://example.test/")
    years = td.years()
    assert "2025/2026" in years
    assert "2026/2027" in years


def test_term_starts_and_ends(lincolnshire_html: str) -> None:
    provider = LincolnshireProvider()
    td = provider.parse(lincolnshire_html)
    starts = {(e.date, e.academic_year) for e in td.events if e.kind == EventKind.TERM_START}
    ends = {(e.date, e.academic_year) for e in td.events if e.kind == EventKind.TERM_END}
    # Term 1, 2025/26
    assert (date(2025, 9, 4), "2025/2026") in starts
    assert (date(2025, 10, 23), "2025/2026") in ends
    # Term 2 — straddling Christmas
    assert (date(2025, 11, 3), "2025/2026") in starts
    assert (date(2025, 12, 19), "2025/2026") in ends
    # Term 6 ends in summer 2026
    assert (date(2026, 7, 22), "2025/2026") in ends
    # New academic year picked up
    assert (date(2026, 9, 3), "2026/2027") in starts


def test_half_term_ranges(lincolnshire_html: str) -> None:
    provider = LincolnshireProvider()
    td = provider.parse(lincolnshire_html)
    starts = {e.date for e in td.events if e.kind == EventKind.HALF_TERM_START}
    ends = {e.date for e in td.events if e.kind == EventKind.HALF_TERM_END}
    assert date(2025, 10, 24) in starts
    assert date(2025, 11, 2) in ends
    assert date(2026, 2, 14) in starts
    assert date(2026, 2, 22) in ends
    assert date(2026, 5, 23) in starts
    assert date(2026, 5, 31) in ends


def test_holiday_events(lincolnshire_html: str) -> None:
    provider = LincolnshireProvider()
    td = provider.parse(lincolnshire_html)
    holiday_starts = {e.date for e in td.events if e.kind == EventKind.HOLIDAY_START}
    holiday_ends = {e.date for e in td.events if e.kind == EventKind.HOLIDAY_END}
    assert date(2025, 12, 20) in holiday_starts  # Christmas holiday
    assert date(2026, 1, 5) in holiday_ends
    assert date(2026, 4, 3) in holiday_starts  # Easter holiday
    assert date(2026, 7, 23) in holiday_starts  # Summer holiday


def test_no_inset_events_at_lea_level(lincolnshire_html: str) -> None:
    """Lincolnshire's published page does not list INSET days at the LEA level
    — those are individual-school decisions and surface in school PD providers."""
    provider = LincolnshireProvider()
    td = provider.parse(lincolnshire_html)
    insets = [e for e in td.events if e.kind == EventKind.INSET]
    assert insets == []
