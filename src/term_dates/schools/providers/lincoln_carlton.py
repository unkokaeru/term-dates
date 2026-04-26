"""PD-day provider for Lincoln Carlton Academy (URN 142037).

The school's term-dates page is an attachment listing — the actual dates
live in PDF files served via ``download.asp?file=N&type=pdf`` links. The
provider scans the listing for the most-recent term-dates PDF, extracts
its text (these PDFs are textual, not image-based), then runs the
generic PD-day extractor.
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from term_dates.models import PDDay, School, SchoolPhase
from term_dates.parsing import current_academic_year_start
from term_dates.schools._extract import extract_pd_days, html_to_text, pdf_to_text
from term_dates.schools.base import PDDayProvider

URL = "https://www.lincolncarlton.anthemtrust.uk/term-dates-and-school-times"

_YEAR_PAIR_RE = re.compile(r"(20\d{2})\s*[-–to ]+\s*(20\d{2}|\d{2})")


class LincolnCarltonProvider(PDDayProvider):
    school = School(
        urn="142037",
        name="Lincoln Carlton Academy",
        lea_code="925",
        lea_name="Lincolnshire",
        phase=SchoolPhase.PRIMARY,
        town="Lincoln",
        postcode="LN2 4WA",
        website="https://www.lincolncarlton.anthemtrust.uk/",
    )
    source_url = URL

    def fetch(self) -> tuple[PDDay, ...]:
        html = self.fetcher.get_text(URL)
        pdf_url = self._pick_pdf_url(html)
        if pdf_url is None:
            # Page itself sometimes contains parseable text — try that first.
            return self.parse(html)
        try:
            pdf_bytes = self.fetcher.get_bytes(pdf_url)
        except Exception:  # noqa: BLE001 — graceful degradation
            return self.parse(html)
        return self.parse(pdf_to_text(pdf_bytes))

    def parse(self, body: str, *, default_year: int | None = None) -> tuple[PDDay, ...]:
        text = html_to_text(body) if "<" in body and ">" in body else body
        return extract_pd_days(
            text,
            default_year=default_year or current_academic_year_start(),
            source_label="Lincoln Carlton",
        )

    @staticmethod
    def _pick_pdf_url(html: str) -> str | None:
        """Find the term-dates PDF most relevant to today.

        Prefer the PDF whose start year equals the current academic-year
        start (so on 26 Apr 2026 we pick the 2025-26 PDF). Fall back to the
        most-recent PDF if no exact match exists.
        """
        soup = BeautifulSoup(html, "lxml")
        candidates: list[tuple[int, str]] = []
        for anchor in soup.find_all("a", href=True):
            href_attr = anchor["href"]
            href = href_attr if isinstance(href_attr, str) else " ".join(href_attr)
            if "download.asp" not in href.lower() or "type=pdf" not in href.lower():
                continue
            title_attr = anchor.get("title") or ""
            title_str = title_attr if isinstance(title_attr, str) else " ".join(title_attr)
            label = (anchor.get_text(" ", strip=True) or title_str).lower()
            if "term dates" not in label:
                continue
            year_match = _YEAR_PAIR_RE.search(label)
            year = int(year_match.group(1)) if year_match else 0
            absolute = urljoin(URL, href)
            candidates.append((year, absolute))
        if not candidates:
            return None
        return _pick_best_year(candidates)


def _pick_best_year(candidates: list[tuple[int, str]]) -> str | None:
    """Choose the PDF whose start-year matches today's academic year.

    Returns the URL string, or None when ``candidates`` is empty. When more
    than one entry shares the chosen start-year, the first listed wins (HTML
    source order — typically the most prominent on the page).
    """
    if not candidates:
        return None
    today_start = current_academic_year_start()
    for year, url_ in candidates:
        if year == today_start:
            return url_
    candidates_sorted = sorted(candidates, key=lambda t: t[0], reverse=True)
    return candidates_sorted[0][1]
