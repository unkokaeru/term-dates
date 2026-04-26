"""Best-effort PD-day provider for any school with a published website.

Auto-registered for any :class:`~term_dates.models.School` whose ``website``
is set when no curated provider exists for that URN. The flow:

1. Try a small set of common term-date URL paths under the school's website
   (``/term-dates/``, ``/key-information/term-dates/`` etc.).
2. Run :func:`extract_pd_days` over each candidate page.
3. Return the first non-empty result, or fall back to the homepage.

Errors are swallowed silently — many school sites are 404 / WAF-blocked /
JavaScript-rendered, so noise would drown out useful output.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

import httpx

from term_dates.http import Fetcher
from term_dates.models import PDDay, School
from term_dates.parsing import current_academic_year_start
from term_dates.schools._extract import extract_pd_days, html_to_text, pdf_to_text
from term_dates.schools.base import PDDayProvider

# Common URL slugs UK schools use for term/INSET pages.
_PROBE_PATHS: tuple[str, ...] = (
    "/term-dates/",
    "/term-dates",
    "/parents/term-dates/",
    "/parents/term-dates",
    "/key-information/term-dates/",
    "/key-information/term-dates",
    "/about-us/term-dates/",
    "/about/term-dates/",
    "/calendar/",
    "/key-dates/",
    "/diary-dates/",
    "/inset-days/",
    "/parents/inset-days/",
    "/term-dates-and-school-times",
    "/term-dates-and-holidays/",
)

_PDF_LINK_RE = re.compile(
    r'href=["\']([^"\']+\.pdf)["\']',
    flags=re.IGNORECASE,
)


class GenericSchoolPDProvider(PDDayProvider):
    """Probe a school's site for any page that mentions PD/INSET dates."""

    def __init__(self, school: School, fetcher: Fetcher | None = None) -> None:
        super().__init__(fetcher)
        self.school = school
        self.source_url = school.website or ""

    def fetch(self) -> tuple[PDDay, ...]:
        if not self.school.website:
            return ()
        default_year = current_academic_year_start()

        # Try targeted paths in order; stop on first hit.
        for path in _PROBE_PATHS:
            url = urljoin(self.school.website, path)
            html = self._safe_get(url)
            if html is None:
                continue
            days = self._parse_with_pdf_fallback(html, url, default_year)
            if days:
                self.source_url = url
                return days

        # Fall back to the homepage itself.
        home = self._safe_get(self.school.website)
        if home is None:
            return ()
        days = self._parse_with_pdf_fallback(home, self.school.website, default_year)
        return days

    def parse(self, html: str, *, default_year: int | None = None) -> tuple[PDDay, ...]:
        return extract_pd_days(
            html_to_text(html),
            default_year=default_year or current_academic_year_start(),
            source_label=self.school.name,
        )

    # -----------------------------------------------------------------

    def _safe_get(self, url: str) -> str | None:
        try:
            return self.fetcher.get_text(url)
        except httpx.HTTPError:
            return None

    def _parse_with_pdf_fallback(
        self, html: str, base_url: str, default_year: int
    ) -> tuple[PDDay, ...]:
        """Extract from HTML, then if empty try the most plausible PDF link."""
        days = self.parse(html, default_year=default_year)
        if days:
            return days
        # Look for a PDF whose URL or surrounding text mentions term dates.
        for match in _PDF_LINK_RE.finditer(html):
            href = match.group(1)
            if "term" not in href.lower() and "date" not in href.lower():
                continue
            pdf_url = urljoin(base_url, href)
            try:
                pdf_bytes = self.fetcher.get_bytes(pdf_url)
            except httpx.HTTPError:
                continue
            pdf_days = extract_pd_days(
                pdf_to_text(pdf_bytes),
                default_year=default_year,
                source_label=self.school.name,
            )
            if pdf_days:
                self.source_url = pdf_url
                return pdf_days
        return ()
