"""Test the Lincolnshire LEA term-dates parser against a fixture HTML page."""

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
    assert (date(2025, 9, 3), "2025/2026") in starts
    assert (date(2025, 12, 19), "2025/2026") in ends
    assert (date(2026, 1, 5), "2025/2026") in starts
    assert (date(2026, 7, 17), "2025/2026") in ends
    assert (date(2026, 9, 2), "2026/2027") in starts


def test_inset_days(lincolnshire_html: str) -> None:
    provider = LincolnshireProvider()
    td = provider.parse(lincolnshire_html)
    insets = {e.date for e in td.events if e.kind == EventKind.INSET}
    # Two INSETs in autumn 2025, one in spring 2026, one in summer 2026,
    # one in autumn 2026 = 5 total.
    assert date(2025, 9, 1) in insets
    assert date(2025, 9, 2) in insets
    assert date(2026, 2, 13) in insets
    assert date(2026, 7, 20) in insets
    assert date(2026, 9, 1) in insets


def test_half_term_ranges(lincolnshire_html: str) -> None:
    provider = LincolnshireProvider()
    td = provider.parse(lincolnshire_html)
    starts = {e.date for e in td.events if e.kind == EventKind.HALF_TERM_START}
    ends = {e.date for e in td.events if e.kind == EventKind.HALF_TERM_END}
    assert date(2025, 10, 27) in starts
    assert date(2025, 10, 31) in ends
    assert date(2026, 2, 16) in starts
    assert date(2026, 2, 20) in ends
    assert date(2026, 5, 25) in starts
    assert date(2026, 5, 29) in ends
