"""Lincolnshire County Council term-dates provider.

Source page:
    https://www.lincolnshire.gov.uk/school-attendance/school-term-times

The page is organised into ``<h2>`` headings per academic year (e.g.
``Academic year 2025 to 2026``), each followed by ``<h3>`` sub-headings for
each term and an unordered list of dated bullets such as
``Term starts: Wednesday 3 September 2025``. Lincolnshire's published dates
apply to community and voluntary-controlled schools only — academies, free
schools and voluntary-aided schools may differ, so per-school PD-day pollers
exist in :mod:`term_dates.schools.providers`.
"""

from __future__ import annotations

import re
from datetime import date as _date

from bs4 import BeautifulSoup

from term_dates.lea.base import LEAProvider
from term_dates.models import LEA, AcademicEvent, EventKind, TermDates
from term_dates.parsing import parse_uk_date, parse_uk_date_range

URL = "https://www.lincolnshire.gov.uk/school-attendance/school-term-times"

LEA_INFO = LEA(
    code="925",  # Lincolnshire's well-known DfE LA code
    name="Lincolnshire",
    region="East Midlands",
    term_dates_url=URL,
)


_YEAR_HEADING_RE = re.compile(
    r"academic\s+year[^0-9]*([12][0-9]{3})\s*(?:/|to|-)\s*([12][0-9]{3})",
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

        for node in soup.find_all(["h2", "h3", "li", "p"]):
            text = node.get_text(" ", strip=True)
            if not text:
                continue
            if node.name in {"h2", "h3"}:
                year_match = _YEAR_HEADING_RE.search(text)
                if year_match:
                    current_year = f"{year_match.group(1)}/{year_match.group(2)}"
                continue
            if current_year is None:
                continue
            events.extend(_parse_bullet(text, current_year))

        return TermDates(
            lea_code=self.lea.code,
            lea_name=self.lea.name,
            source_url=source_url or URL,
            events=tuple(events),
        )


# Bullet patterns we expect to see on the page.
_TERM_LABELS = {
    "autumn term": (EventKind.TERM_START, EventKind.TERM_END),
    "spring term": (EventKind.TERM_START, EventKind.TERM_END),
    "summer term": (EventKind.TERM_START, EventKind.TERM_END),
}

_HALF_TERM_LABELS = ("half term", "half-term")
_INSET_LABELS = ("inset", "training day", "non-pupil", "occasional day", "pd day")

_RANGE_HINT = re.compile(r"\b(?:to|–|—|-|until|through)\b", flags=re.IGNORECASE)


def _parse_bullet(text: str, academic_year: str) -> list[AcademicEvent]:
    """Map a single bullet string to zero or more AcademicEvents."""
    lower = text.lower()
    out: list[AcademicEvent] = []

    # 1) "Autumn term: Wed 3 Sep 2025 to Fri 19 Dec 2025"
    for label, (start_kind, end_kind) in _TERM_LABELS.items():
        if label in lower:
            rng = _maybe_parse_range(text)
            if rng is not None:
                start, end = rng
                title = label.title()
                out.append(AcademicEvent(start, start_kind, f"{title} starts", academic_year))
                out.append(AcademicEvent(end, end_kind, f"{title} ends", academic_year))
                return out

    # 2) "Half term: Mon 27 Oct to Fri 31 Oct 2025"
    if any(h in lower for h in _HALF_TERM_LABELS):
        rng = _maybe_parse_range(text)
        if rng is not None:
            start, end = rng
            out.append(
                AcademicEvent(start, EventKind.HALF_TERM_START, "Half term starts", academic_year)
            )
            out.append(
                AcademicEvent(end, EventKind.HALF_TERM_END, "Half term ends", academic_year)
            )
            return out

    # 3) "Inset day: Tuesday 2 September 2025"
    if any(i in lower for i in _INSET_LABELS):
        when = _maybe_parse_single(text)
        if when is not None:
            out.append(AcademicEvent(when, EventKind.INSET, text, academic_year))
            return out

    # 4) Generic "Term starts ..." / "Term ends ..." sentences
    if "term start" in lower:
        when = _maybe_parse_single(text)
        if when is not None:
            out.append(AcademicEvent(when, EventKind.TERM_START, text, academic_year))
            return out
    if "term end" in lower:
        when = _maybe_parse_single(text)
        if when is not None:
            out.append(AcademicEvent(when, EventKind.TERM_END, text, academic_year))

    return out


def _maybe_parse_range(text: str) -> tuple[_date, _date] | None:
    if not _RANGE_HINT.search(text):
        return None
    return parse_uk_date_range(_strip_label(text))


def _maybe_parse_single(text: str) -> _date | None:
    return parse_uk_date(_strip_label(text))


def _strip_label(text: str) -> str:
    """Remove a leading "Foo:" or "Foo -" label so the date string parses cleanly."""
    return re.sub(r"^[^:–\-]{0,80}[:–\-]\s*", "", text, count=1)
