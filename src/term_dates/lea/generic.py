"""Generic, best-effort LEA term-date provider.

Auto-registered in :mod:`term_dates.lea.registry` for every LEA in the
registry that has a ``term_dates_url`` but no bespoke provider class. The
underlying parser lives in :mod:`term_dates.lea._generic_extract`.

Fetch flow:

1. Try the declared ``term_dates_url`` and parse it.
2. If that yields nothing useful, scan the response for in-page links whose
   href or anchor text contains "term", "school year", "calendar", or
   "holiday", and try them in turn (capped to keep latency sane).
3. Give up gracefully and return an empty :class:`TermDates` — the CLI/UI
   already render that as "no events" rather than a hard error.

This is explicitly best-effort: UK council pages vary so widely that the
generic parser will produce empty / partial / occasionally wrong results
on a meaningful fraction of councils. The CLI marks generic-backed LEAs
distinctly so users know which entries are curated and which are auto.
"""

from __future__ import annotations

from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from term_dates.http import Fetcher
from term_dates.lea._generic_extract import parse_lea_html
from term_dates.lea.base import LEAProvider
from term_dates.models import LEA, AcademicEvent, TermDates

_LINK_KEYWORDS = (
    "term date",
    "term dates",
    "school term",
    "school year",
    "term and holiday",
    "term-dates",
    "school-term",
    "school-holiday",
    "inset",
    "calendar",
    "key dates",
)
_MAX_LINK_FOLLOWS = 4


class GenericLEAProvider(LEAProvider):
    """Fetch + parse any LEA's published term-dates URL with shared heuristics."""

    def __init__(self, lea: LEA, fetcher: Fetcher | None = None) -> None:
        super().__init__(fetcher)
        # Instance-level: the base class only declares `lea: LEA` as annotation.
        self.lea = lea

    def fetch(self) -> TermDates:
        url = self.lea.term_dates_url or ""
        if not url:
            return self._empty(source="")
        # Primary fetch: HTTP errors propagate so the aggregate command can
        # classify them as failures instead of silent zero-event successes.
        html = self.fetcher.get_text(url)
        events = parse_lea_html(html)
        if events:
            return self._make(tuple(events), source=url)

        # Fallback: follow likely term-date links on the page (errors swallowed
        # — these are trial-and-error attempts).
        for candidate in _find_candidate_links(html, base_url=url)[:_MAX_LINK_FOLLOWS]:
            sub_html = self._safe_get(candidate)
            if sub_html is None:
                continue
            sub_events = parse_lea_html(sub_html)
            if sub_events:
                return self._make(tuple(sub_events), source=candidate)

        return self._empty(source=url)

    def parse(self, html: str, *, source_url: str | None = None) -> TermDates:
        events = parse_lea_html(html)
        return self._make(tuple(events), source=source_url or self.lea.term_dates_url or "")

    # -----------------------------------------------------------------

    def _safe_get(self, url: str) -> str | None:
        try:
            return self.fetcher.get_text(url)
        except httpx.HTTPError:
            return None

    def _make(self, events: tuple[AcademicEvent, ...], *, source: str) -> TermDates:
        return TermDates(
            lea_code=self.lea.code,
            lea_name=self.lea.name,
            source_url=source,
            events=events,
        )

    def _empty(self, *, source: str) -> TermDates:
        return self._make((), source=source)


def _find_candidate_links(html: str, *, base_url: str) -> list[str]:
    """Return absolute URLs of in-page anchors that look term-date related.

    Ranked by anchor-text relevance: links whose visible text contains one
    of :data:`_LINK_KEYWORDS` come first, then links whose href slug does.
    """
    soup = BeautifulSoup(html, "lxml")
    text_hits: list[str] = []
    href_hits: list[str] = []
    for anchor in soup.find_all("a", href=True):
        if not isinstance(anchor, Tag):
            continue
        href_attr = anchor["href"]
        href = href_attr if isinstance(href_attr, str) else " ".join(href_attr)
        if href.startswith("#") or href.lower().startswith(("javascript:", "mailto:")):
            continue
        text = anchor.get_text(" ", strip=True).lower()
        href_lc = href.lower()
        absolute = urljoin(base_url, href)
        if any(k in text for k in _LINK_KEYWORDS):
            text_hits.append(absolute)
        elif any(
            k.replace(" ", "-") in href_lc or k.replace(" ", "_") in href_lc
            for k in _LINK_KEYWORDS
        ):
            href_hits.append(absolute)
    seen: set[str] = set()
    out: list[str] = []
    for url in [*text_hits, *href_hits]:
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
    return out


__all__ = ["GenericLEAProvider"]
