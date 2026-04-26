"""Best-effort extraction of LEA term-date events from arbitrary HTML.

This is the shared engine behind :class:`term_dates.lea.generic.GenericLEAProvider`,
which auto-registers for every LEA in the registry that has a published URL but
no bespoke parser. UK council pages vary widely — table layouts, bulleted
lists, prose paragraphs — so the parser tries each shape and keeps whatever
events fall out. It never raises; it returns ``[]`` when nothing parses.

Heuristics:

* Track the most recent academic-year heading (``2025/2026``,
  ``2025 to 26``, ``Academic year 2025-2026``) so events emitted for a
  given section get the right year.
* Walk every ``<table>`` and try each row as
  ``(label, start_date, end_date)``. When only one date cell is parseable,
  emit a single-date event. When the cell itself contains a "X to Y" range,
  try :func:`parse_uk_date_range`.
* Walk top-level ``<ul>`` / ``<ol>`` items and parse each ``<li>``.
* Bucket events into kinds (term, half-term, holiday, INSET) by keyword
  match on the row label; fall back to TERM_START / TERM_END.
"""

from __future__ import annotations

import re
from datetime import date

from bs4 import BeautifulSoup, Tag

from term_dates.models import AcademicEvent, EventKind
from term_dates.parsing import parse_uk_date, parse_uk_date_range

_YEAR_HEADING_RE = re.compile(
    r"(?P<start>20\d{2})\s*(?:/|to|-|–|—)\s*(?P<end>20\d{2}|\d{2})",
    flags=re.IGNORECASE,
)

_HALF_TERM_LABELS = ("half term", "half-term", "midterm", "mid-term")
_HOLIDAY_LABELS = (
    "holiday",
    "break",
    "vacation",
    "christmas",
    "easter",
    "summer holiday",
    "winter break",
    "spring break",
)
_INSET_LABELS = (
    "inset",
    "training day",
    "non-pupil",
    "non pupil",
    "occasional day",
    "pd day",
    "professional development",
    "teacher training",
    "staff training",
    "staff day",
)
_TERM_LABELS = (
    "term",
    "autumn",
    "spring",
    "summer",
    "michaelmas",
    "lent",
    "trinity",
)


def parse_lea_html(html: str) -> list[AcademicEvent]:
    """Pull every dated academic event we can recognise out of an HTML page."""
    soup = BeautifulSoup(html, "lxml")

    fallback_year = _find_year_anywhere(soup)
    events: list[AcademicEvent] = []
    current_year = fallback_year

    for node in soup.find_all(["h1", "h2", "h3", "h4", "h5", "table", "ul", "ol"]):
        if not isinstance(node, Tag):
            continue
        if node.name in {"h1", "h2", "h3", "h4", "h5"}:
            year = _academic_year_from_text(node.get_text(" ", strip=True))
            if year is not None:
                current_year = year
            continue
        if current_year is None:
            continue
        if node.name == "table":
            events.extend(_parse_table(node, current_year))
        else:
            events.extend(_parse_list(node, current_year))

    return _dedupe(events)


def _academic_year_from_text(text: str) -> str | None:
    match = _YEAR_HEADING_RE.search(text)
    if match is None:
        return None
    start = int(match.group("start"))
    end_raw = match.group("end")
    end = int(end_raw) if len(end_raw) == 4 else 2000 + int(end_raw)
    if end <= start:
        end = start + 1
    if end - start != 1:
        return None  # something like "2024/2030" isn't an academic year
    return f"{start}/{end}"


def _find_year_anywhere(soup: BeautifulSoup) -> str | None:
    """Last-ditch fallback: look at title and the first few headings."""
    candidates: list[Tag] = []
    if soup.title is not None and isinstance(soup.title, Tag):
        candidates.append(soup.title)
    for tag in soup.find_all(["h1", "h2", "h3"], limit=10):
        if isinstance(tag, Tag):
            candidates.append(tag)
    for tag in candidates:
        year = _academic_year_from_text(tag.get_text(" ", strip=True))
        if year is not None:
            return year
    return None


def _parse_table(table: Tag, academic_year: str) -> list[AcademicEvent]:
    out: list[AcademicEvent] = []
    for row in table.find_all("tr"):
        if not isinstance(row, Tag):
            continue
        cells = row.find_all(["th", "td"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(" ", strip=True)
        rest = [c.get_text(" ", strip=True) for c in cells[1:]]
        if not label:
            continue
        # Skip table-header rows like "Term | Starts | Ends"
        if all(_looks_like_header_word(c) for c in rest):
            continue
        # 3+ cells: label | start | end
        if len(rest) >= 2:
            start = parse_uk_date(rest[0])
            end = parse_uk_date(rest[1])
            if start is not None or end is not None:
                out.extend(_emit_for_label(label, start, end, academic_year))
                continue
        # 2 cells: label | <date or range>
        if rest:
            text = rest[0]
            rng = parse_uk_date_range(text)
            if rng is not None:
                out.extend(_emit_for_label(label, rng[0], rng[1], academic_year))
                continue
            d = parse_uk_date(text)
            if d is not None:
                out.extend(_emit_for_label(label, d, None, academic_year))
                continue
    return out


def _parse_list(node: Tag, academic_year: str) -> list[AcademicEvent]:
    out: list[AcademicEvent] = []
    for li in node.find_all("li"):
        if not isinstance(li, Tag):
            continue
        text = li.get_text(" ", strip=True)
        if not text:
            continue
        out.extend(_parse_bullet(text, academic_year))
    return out


def _parse_bullet(text: str, academic_year: str) -> list[AcademicEvent]:
    label = text
    rng = parse_uk_date_range(text)
    if rng is not None:
        return _emit_for_label(label, rng[0], rng[1], academic_year)
    stripped = _strip_label(text)
    d = parse_uk_date(stripped) or parse_uk_date(text)
    if d is not None:
        return _emit_for_label(label, d, None, academic_year)
    return []


def _emit_for_label(
    label: str,
    start: date | None,
    end: date | None,
    academic_year: str,
) -> list[AcademicEvent]:
    lower = label.lower()
    out: list[AcademicEvent] = []

    def _emit(d: date | None, kind: EventKind, suffix: str) -> None:
        if d is not None:
            out.append(AcademicEvent(d, kind, f"{label} {suffix}".strip(), academic_year))

    if any(h in lower for h in _HALF_TERM_LABELS):
        _emit(start, EventKind.HALF_TERM_START, "starts")
        _emit(end, EventKind.HALF_TERM_END, "ends")
        return out
    if any(i in lower for i in _INSET_LABELS):
        _emit(start, EventKind.INSET, "")
        _emit(end, EventKind.INSET, "(end)")
        return out
    if any(h in lower for h in _HOLIDAY_LABELS):
        _emit(start, EventKind.HOLIDAY_START, "starts")
        _emit(end, EventKind.HOLIDAY_END, "ends")
        return out
    if any(t in lower for t in _TERM_LABELS):
        _emit(start, EventKind.TERM_START, "starts")
        _emit(end, EventKind.TERM_END, "ends")
        return out

    # Unknown label — best-effort term emission so the user at least sees it.
    _emit(start, EventKind.TERM_START, "")
    _emit(end, EventKind.TERM_END, "(end)")
    return out


def _looks_like_header_word(text: str) -> bool:
    t = text.strip().lower()
    return t in {
        "starts",
        "start",
        "ends",
        "end",
        "from",
        "to",
        "date",
        "dates",
        "first day",
        "last day",
    }


def _strip_label(text: str) -> str:
    return re.sub(r"^[^:–\-]{0,80}[:–\-]\s*", "", text, count=1)


def _dedupe(events: list[AcademicEvent]) -> list[AcademicEvent]:
    """Drop exact duplicates while preserving order."""
    seen: set[tuple[date, EventKind, str]] = set()
    out: list[AcademicEvent] = []
    for e in events:
        key = (e.date, e.kind, e.academic_year)
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out
