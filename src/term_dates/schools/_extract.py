"""Generic extraction of PD/INSET days from a school calendar page or PDF.

School websites publish their term dates and PD days in wildly different
formats — tables, bullet lists, prose paragraphs, calendar widgets. The one
thing they all share is that PD days are labelled near a specific calendar
date, with the label drawn from a small vocabulary ("INSET", "PD day",
"training day", "non-pupil day", etc.).

This module turns plain text from any source into a tuple of :class:`PDDay`.
"""

from __future__ import annotations

import io
import re
from collections.abc import Iterable
from datetime import date

from bs4 import BeautifulSoup

from term_dates.models import PDDay
from term_dates.parsing import academic_year_for, looks_like_pd_day

# A liberal date matcher that handles the dozens of UK conventions schools use.
# Notable real-world quirks accommodated:
#   - "3rd September" / "3 rd September" (suffix glued or with intervening space)
#   - "Mon 27 Oct" / "Monday 27th October" / "27/10/2025"
#   - "23 to 26 March 2026" (the ranges are split downstream)
_DATE_RE = re.compile(
    r"""
    (?:(?:Mon|Tue|Tues|Wed|Wednes|Thu|Thur|Thurs|Fri|Sat|Sun)[a-z]*\.?,?\s+)?  # optional day name
    (?P<day>\d{1,2})
    (?:\s*(?:st|nd|rd|th))?
    \s*
    (?:[ /\-,]|of\s+)?
    \s*
    (?P<month>
        Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
        Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|
        Nov(?:ember)?|Dec(?:ember)?
    )
    \s*,?\s*
    (?P<year>20\d{2})?
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


def html_to_text(html: str) -> str:
    """Reduce HTML to plain text suitable for the PD-day extractor."""
    soup = BeautifulSoup(html, "lxml")
    # Tables: render row-by-row with " | " separators so "INSET" and the date
    # in adjacent <td>s end up on the same line.
    out_lines: list[str] = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
            joined = " | ".join(c for c in cells if c)
            if joined:
                out_lines.append(joined)
        table.decompose()
    # Everything else: each block-level element on its own line.
    for block in soup.find_all(["p", "li", "h1", "h2", "h3", "h4", "tr", "div"]):
        text = block.get_text(" ", strip=True)
        if text:
            out_lines.append(text)
    return "\n".join(out_lines)


def pdf_to_text(data: bytes) -> str:
    """Extract text from a PDF byte stream.

    Schools commonly publish term dates as PDFs. We use pypdf, which is pure
    Python and handles most parent-newsletter-style PDFs. Each page becomes a
    block of lines; lines are kept in source order so adjacent labels and dates
    stay together for the PD-day extractor.
    """
    from pypdf import PdfReader  # imported lazily; pypdf is heavy to import

    reader = PdfReader(io.BytesIO(data))
    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 — malformed pages should not abort the document
            pages.append("")
    return "\n".join(pages)


_PD_CONTEXT_LOOKAHEAD = 3  # max number of lines after a PD-keyword line we still credit

_LINE_STARTS_WITH_DATE_RE = re.compile(
    r"^\s*(?:(?:Mon|Tue|Tues|Wed|Wednes|Thu|Thur|Thurs|Fri|Sat|Sun)[a-z]*\.?,?\s+)?"
    r"\d{1,2}",
    flags=re.IGNORECASE,
)


def extract_pd_days(
    text: str, *, default_year: int | None = None, source_label: str = ""
) -> tuple[PDDay, ...]:
    """Return all PD/INSET dates found in ``text``.

    Two pickups happen here:

    1. Direct: a line mentions a PD-day keyword *and* contains at least one
       parseable date — emit one :class:`PDDay` per parsed date.
    2. Spillover: a line mentions a PD-day keyword but has no parseable date
       (common in PDFs, where the label wraps onto its own line). The next
       few "bare-date" lines (lines beginning with a weekday or digit) are
       credited to that label. The window closes as soon as a line with a
       different non-date label appears (e.g. ``"First day in school..."``)
       or after :data:`_PD_CONTEXT_LOOKAHEAD` non-empty lines.
    """
    seen: set[tuple[date, str]] = set()
    out: list[PDDay] = []
    lines = [raw.strip() for raw in text.splitlines()]

    pending_label: str | None = None
    pending_remaining: int = 0

    for line in lines:
        if not line:
            pending_label = None
            pending_remaining = 0
            continue

        line_dates = list(_iter_dates(line, default_year=default_year))
        if looks_like_pd_day(line):
            label_for_line = _clean_label(line, source_label)
            for d in line_dates:
                _emit(out, seen, d, label_for_line)
            # Always open a short spillover window — sibling dates on the next
            # lines may still be part of the same PD-day group (e.g. the second
            # of two INSET days that wrapped onto its own line in a PDF).
            pending_label = label_for_line
            pending_remaining = _PD_CONTEXT_LOOKAHEAD
            continue

        if pending_label is None:
            continue

        if line_dates and not _LINE_STARTS_WITH_DATE_RE.match(line):
            # The line carries a date but starts with a different label
            # (e.g. "First day in school for pupils Tuesday 5th January…")
            # — close the spillover without crediting it.
            pending_label = None
            pending_remaining = 0
            continue

        for d in line_dates:
            _emit(out, seen, d, pending_label)
        pending_remaining -= 1
        if pending_remaining <= 0:
            pending_label = None

    out.sort(key=lambda p: p.date)
    return tuple(out)


def _emit(
    out: list[PDDay],
    seen: set[tuple[date, str]],
    d: date,
    label: str,
) -> None:
    year = academic_year_for(d)
    key = (d, year)
    if key in seen:
        return
    seen.add(key)
    out.append(PDDay(date=d, label=label, academic_year=year))


_WEEKDAY_PREFIX = (
    r"(?:Mon|Tue|Tues|Wed|Wednes|Thu|Thur|Thurs|Fri|Sat|Sun)[a-z]*\.?,?\s+"
)

# Matches a lonely "<weekday> <day>(<ordinal>)?" with no month immediately
# following — used to pick up "Thursday 3 rd and Friday 4 th September 2026"
# where only the second day is glued to the month.
_LONELY_DAY_RE = re.compile(
    r"(?<![A-Za-z0-9])" + _WEEKDAY_PREFIX +
    r"(?P<day>\d{1,2})(?:\s*(?:st|nd|rd|th))?\b",
    flags=re.IGNORECASE,
)


def _iter_dates(line: str, default_year: int | None) -> Iterable[date]:
    """Yield every parseable date in ``line``.

    Two-pass approach:

    1. Pull every full ``<day> <month> [<year>]`` match. When a match is
       missing the year, inherit it from the next dated sibling on the same
       line ("3 and 4 September 2026" — the 3rd inherits 2026).
    2. Find any "lonely" ``<weekday> <day>`` tokens that *don't* sit inside
       a full-date match, and inherit the month/year of the next full-date
       on the same line. This is what makes "Thursday 3 rd and Friday 4 th
       September 2026" emit two dates instead of one.
    """
    full_matches = list(_DATE_RE.finditer(line))

    # Forward-fill years so earlier yearless full matches inherit later ones.
    fill_year: list[int | None] = [None] * len(full_matches)
    next_year: int | None = None
    for i in range(len(full_matches) - 1, -1, -1):
        y = full_matches[i].group("year")
        if y is not None:
            next_year = int(y)
        fill_year[i] = next_year if next_year is not None else default_year

    emitted: list[date] = []
    full_match_spans: list[tuple[int, int]] = []
    for match, year in zip(full_matches, fill_year, strict=False):
        full_match_spans.append(match.span())
        day = int(match.group("day"))
        month_word = match.group("month").lower()[:3]
        month = _MONTH_INDEX.get(month_word)
        explicit_year = match.group("year")
        chosen_year = int(explicit_year) if explicit_year is not None else year
        if month is None or chosen_year is None:
            continue
        try:
            emitted.append(date(chosen_year, month, day))
        except ValueError:
            continue

    # Now lonely-day pickups: weekdays + day numbers that aren't already
    # consumed by a full match, paired with the next full-match's month/year.
    for lonely in _LONELY_DAY_RE.finditer(line):
        s, e = lonely.span()
        if any(fs <= s < fe for fs, fe in full_match_spans):
            continue
        # Find the next full-match-with-month after this lonely position.
        host: tuple[int, int] | None = None
        for match, year in zip(full_matches, fill_year, strict=False):
            if match.start() < e:
                continue
            month_word = match.group("month").lower()[:3]
            month = _MONTH_INDEX.get(month_word)
            explicit_year = match.group("year")
            chosen_year = int(explicit_year) if explicit_year is not None else year
            if month is None or chosen_year is None:
                continue
            host = (month, chosen_year)
            break
        if host is None:
            continue
        host_month, host_year = host
        try:
            emitted.append(date(host_year, host_month, int(lonely.group("day"))))
        except ValueError:
            continue

    emitted.sort()
    seen: set[date] = set()
    for d in emitted:
        if d in seen:
            continue
        seen.add(d)
        yield d


_MONTH_INDEX: dict[str, int] = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _clean_label(line: str, source_label: str) -> str:
    label = re.sub(r"\s+", " ", line).strip(" -|:")
    if len(label) > 140:
        label = label[:137].rstrip() + "…"
    if source_label:
        return f"{source_label}: {label}"
    return label
