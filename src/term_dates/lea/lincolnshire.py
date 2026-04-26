"""Lincolnshire County Council term-dates provider.

Source page:
    https://www.lincolnshire.gov.uk/school-attendance/school-term-times

The live page is organised into ``<h3>`` headings per school year (e.g.
``2025 to 26 school year``) — note that the trailing year is sometimes
abbreviated to two digits. Each heading is followed by a single table per
season (Autumn / Spring / Summer) with rows of the form

    | Term 1   | Thursday, 4 September 2025 | Thursday, 23 October 2025  |
    | Half term| Friday, 24 October 2025    | Sunday, 2 November 2025    |
    | Term 2   | Monday, 3 November 2025    | Friday, 19 December 2025   |
    | Christmas holiday | ...

Lincolnshire's published dates apply to community and voluntary-controlled
schools only — academies, free schools and voluntary-aided schools may
differ, so per-school PD-day pollers exist in
:mod:`term_dates.schools.providers`.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from term_dates.lea.base import LEAProvider
from term_dates.models import LEA, AcademicEvent, EventKind, TermDates
from term_dates.parsing import parse_uk_date

URL = "https://www.lincolnshire.gov.uk/school-attendance/school-term-times"

LEA_INFO = LEA(
    code="925",  # Lincolnshire's well-known DfE LA code
    name="Lincolnshire",
    region="East Midlands",
    term_dates_url=URL,
)


# Matches "2025 to 2026", "2025 to 26", "2025/2026", "Academic year 2025 to 26",
# tolerating non-breaking spaces and stray decorations between the years.
_YEAR_HEADING_RE = re.compile(
    r"(?P<start>20\d{2})\s*[ \s]*(?:/|to|-|–|—)\s*(?P<end>20\d{2}|\d{2})",
    flags=re.IGNORECASE,
)


class LincolnshireProvider(LEAProvider):
    """Term-dates provider for Lincolnshire County Council."""

    lea = LEA_INFO

    def fetch(self) -> TermDates:
        html = self.fetcher.get_text(URL)
        return self.parse(html, source_url=URL)

    def parse(self, html: str, *, source_url: str | None = None) -> TermDates:
        soup = BeautifulSoup(html, "lxml")
        events: list[AcademicEvent] = []
        current_year: str | None = None

        # Walk the document in document order, tracking the most recent
        # academic-year heading and processing every <table> we encounter.
        for node in soup.find_all(["h1", "h2", "h3", "h4", "table"]):
            if not isinstance(node, Tag):
                continue
            if node.name in {"h1", "h2", "h3", "h4"}:
                heading_text = node.get_text(" ", strip=True)
                year = _academic_year_from_heading(heading_text)
                if year is not None:
                    current_year = year
                continue
            if current_year is None:
                continue
            events.extend(_parse_table(node, current_year))

        return TermDates(
            lea_code=self.lea.code,
            lea_name=self.lea.name,
            source_url=source_url or URL,
            events=tuple(events),
        )


def _academic_year_from_heading(text: str) -> str | None:
    match = _YEAR_HEADING_RE.search(text)
    if match is None:
        return None
    start = int(match.group("start"))
    end_raw = match.group("end")
    end = int(end_raw) if len(end_raw) == 4 else 2000 + int(end_raw)
    if end <= start:
        end = start + 1
    return f"{start}/{end}"


# Row-label vocabulary on the live page.
_HALF_TERM_LABELS = ("half term", "half-term")
_HOLIDAY_LABELS = ("holiday",)  # christmas/easter/summer holidays
_INSET_LABELS = ("inset", "training day", "non-pupil", "occasional day", "pd day")


def _parse_table(table: Tag, academic_year: str) -> list[AcademicEvent]:
    """Extract events from one season-table on the Lincolnshire page."""
    out: list[AcademicEvent] = []
    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 3:
            continue
        label = cells[0].get_text(" ", strip=True)
        start_text = cells[1].get_text(" ", strip=True)
        end_text = cells[2].get_text(" ", strip=True)
        if not label:
            continue
        lower = label.lower()
        # Skip table-header rows like "Autumn | Starts | Ends".
        if start_text.lower() in {"starts", "start"} and end_text.lower() in {"ends", "end"}:
            continue
        start = parse_uk_date(start_text)
        end = parse_uk_date(end_text)

        if any(h in lower for h in _HALF_TERM_LABELS):
            if start:
                out.append(
                    AcademicEvent(
                        start,
                        EventKind.HALF_TERM_START,
                        "Half term starts",
                        academic_year,
                    )
                )
            if end:
                out.append(
                    AcademicEvent(end, EventKind.HALF_TERM_END, "Half term ends", academic_year)
                )
            continue

        if any(h in lower for h in _HOLIDAY_LABELS):
            if start:
                out.append(
                    AcademicEvent(start, EventKind.HOLIDAY_START, f"{label} starts", academic_year)
                )
            if end:
                out.append(
                    AcademicEvent(end, EventKind.HOLIDAY_END, f"{label} ends", academic_year)
                )
            continue

        if any(i in lower for i in _INSET_LABELS):
            if start:
                out.append(AcademicEvent(start, EventKind.INSET, label, academic_year))
            continue

        # Default: treat any other labelled row (e.g. "Term 1") as a term start/end pair.
        if start:
            out.append(
                AcademicEvent(start, EventKind.TERM_START, f"{label} starts", academic_year)
            )
        if end:
            out.append(
                AcademicEvent(end, EventKind.TERM_END, f"{label} ends", academic_year)
            )

    return out
