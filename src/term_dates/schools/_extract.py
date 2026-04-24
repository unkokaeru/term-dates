"""Generic extraction of PD/INSET days from a school calendar page or PDF.

School websites publish their term dates and PD days in wildly different
formats — tables, bullet lists, prose paragraphs, calendar widgets. The one
thing they all share is that PD days are labelled near a specific calendar
date, with the label drawn from a small vocabulary ("INSET", "PD day",
"training day", "non-pupil day", etc.).

This module turns plain text from any source into a tuple of :class:`PDDay`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date

from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from term_dates.models import PDDay
from term_dates.parsing import academic_year_for, looks_like_pd_day

# A liberal date matcher that handles the dozens of UK conventions schools use.
_DATE_RE = re.compile(
    r"""
    (?:(?:Mon|Tue|Tues|Wed|Wednes|Thu|Thur|Thurs|Fri|Sat|Sun)[a-z]*\.?\s+)?  # optional day name
    (?P<day>\d{1,2})
    (?:st|nd|rd|th)?
    \s*
    (?:[ /\-]|of\s+)?
    \s*
    (?P<month>
        Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
        Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|
        Nov(?:ember)?|Dec(?:ember)?
    )
    \s*
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


def extract_pd_days(
    text: str, *, default_year: int | None = None, source_label: str = ""
) -> tuple[PDDay, ...]:
    """Return all PD/INSET dates found in ``text``.

    Each line of ``text`` is examined; if it mentions a PD-day keyword and
    contains at least one parseable date, one :class:`PDDay` is emitted per
    date on that line.
    """
    seen: set[tuple[date, str]] = set()
    out: list[PDDay] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or not looks_like_pd_day(line):
            continue
        for d in _iter_dates(line, default_year=default_year):
            label = _clean_label(line, source_label)
            year = academic_year_for(d)
            key = (d, year)
            if key in seen:
                continue
            seen.add(key)
            out.append(PDDay(date=d, label=label, academic_year=year))
    out.sort(key=lambda p: p.date)
    return tuple(out)


def _iter_dates(line: str, default_year: int | None) -> Iterable[date]:
    """Yield every parseable date in ``line``."""
    for match in _DATE_RE.finditer(line):
        text = match.group(0)
        year = match.group("year")
        try:
            if year is None and default_year is not None:
                parsed = dateparser.parse(
                    text,
                    dayfirst=True,
                    default=date(default_year, 1, 1),
                )
            else:
                parsed = dateparser.parse(text, dayfirst=True)
            yield parsed.date()
        except (ValueError, OverflowError):
            continue


def _clean_label(line: str, source_label: str) -> str:
    label = re.sub(r"\s+", " ", line).strip(" -|:")
    if len(label) > 140:
        label = label[:137].rstrip() + "…"
    if source_label:
        return f"{source_label}: {label}"
    return label
