"""Tests for the generic LEA HTML extractor and provider.

Covers the two recipe types the parser supports out of the box:
table-based layouts (most modern councils) and bullet-list layouts.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from term_dates.lea._generic_extract import parse_lea_html
from term_dates.lea.generic import GenericLEAProvider, _find_candidate_links
from term_dates.models import LEA, EventKind

FIXTURES = Path(__file__).parent / "fixtures"


def test_extract_from_table_and_list_layouts() -> None:
    html = (FIXTURES / "generic_lea_table.html").read_text(encoding="utf-8")
    events = parse_lea_html(html)
    assert events, "expected at least some events extracted"
    by_kind = {e.kind: [] for e in events}
    for e in events:
        by_kind.setdefault(e.kind, []).append(e)

    starts = {(e.date, e.academic_year) for e in events if e.kind == EventKind.TERM_START}
    ends = {(e.date, e.academic_year) for e in events if e.kind == EventKind.TERM_END}
    assert (date(2025, 9, 3), "2025/2026") in starts
    assert (date(2025, 12, 19), "2025/2026") in ends
    assert (date(2026, 1, 5), "2025/2026") in starts
    assert (date(2026, 9, 2), "2026/2027") in starts

    half_term_starts = {e.date for e in events if e.kind == EventKind.HALF_TERM_START}
    assert date(2025, 10, 27) in half_term_starts
    assert date(2026, 10, 26) in half_term_starts

    holiday_starts = {e.date for e in events if e.kind == EventKind.HOLIDAY_START}
    assert date(2025, 12, 20) in holiday_starts

    insets = {e.date for e in events if e.kind == EventKind.INSET}
    assert date(2026, 1, 5) in insets


def test_generic_provider_parse_method() -> None:
    html = (FIXTURES / "generic_lea_table.html").read_text(encoding="utf-8")
    lea = LEA(
        code="000",
        name="Anywhere",
        region="Anywhere",
        term_dates_url="https://example.test/terms",
    )
    provider = GenericLEAProvider(lea)
    td = provider.parse(html, source_url="https://example.test/terms")
    assert td.lea_name == "Anywhere"
    assert td.source_url == "https://example.test/terms"
    assert "2025/2026" in td.years()
    assert "2026/2027" in td.years()
    assert any(e.kind == EventKind.HALF_TERM_START for e in td.events)


def test_find_candidate_links_ranks_text_over_href() -> None:
    html = """
    <html><body>
        <a href="/random">Privacy</a>
        <a href="/foo-bar/term-dates/">School term dates and INSET</a>
        <a href="/info?id=123">School Year Calendar</a>
        <a href="javascript:void(0)">js link</a>
        <a href="#anchor">anchor</a>
    </body></html>
    """
    candidates = _find_candidate_links(html, base_url="https://example.test/")
    assert candidates, "expected to find at least one candidate"
    # Anchor-text matches should rank above href-only matches.
    assert candidates[0].endswith("/foo-bar/term-dates/") or candidates[0].endswith("/info?id=123")
    # JS / anchor links must be excluded.
    assert all("javascript:" not in c and not c.endswith("#anchor") for c in candidates)
