"""PD-day provider for Lincoln Christ's Hospital School (URN 120636).

The school publishes term dates as a colour-coded PDF calendar grid linked
from its "useful dates" page. The PDF text-extracts to a sequence of bare
day numbers, so explicit INSET dates cannot be reliably mined from it. The
provider therefore:

* fetches the listing page,
* follows the most recent ``Term_Dates_*.pdf`` link,
* pdf-extracts the body and runs the generic PD-day extractor in case a
  future revision adds textual labels.

If extraction yields nothing the provider returns an empty tuple — callers
already render that as "none found" rather than an error. The fixture HTML
remains as the contract for the parse() method (used by tests).
"""

from __future__ import annotations

import re
from urllib.parse import urljoin

from term_dates.models import PDDay, School, SchoolPhase
from term_dates.parsing import current_academic_year_start
from term_dates.schools._extract import extract_pd_days, html_to_text, pdf_to_text
from term_dates.schools.base import PDDayProvider

# Listing page: kept stable by the school despite the 2022_2023 slug; it
# lists every published Term_Dates PDF as a download link.
LISTING_URL = (
    "https://lincolnchristshospitalschool.co.uk"
    "/parents/useful_information_/useful_dates/school_dates_2022_2023.html"
)

_PDF_LINK_RE = re.compile(
    r'href="([^"]*Term_Dates[^"]*\.pdf)"',
    flags=re.IGNORECASE,
)


class LincolnChristsHospitalProvider(PDDayProvider):
    school = School(
        urn="120636",
        name="Lincoln Christ's Hospital School",
        lea_code="925",
        lea_name="Lincolnshire",
        phase=SchoolPhase.SECONDARY,
        town="Lincoln",
        postcode="LN2 4PN",
        website="https://lincolnchristshospitalschool.co.uk/",
    )
    source_url = LISTING_URL

    def fetch(self) -> tuple[PDDay, ...]:
        listing = self.fetcher.get_text(LISTING_URL)
        pdf_url = self._pick_pdf_url(listing)
        if pdf_url is None:
            return ()
        try:
            pdf_bytes = self.fetcher.get_bytes(pdf_url)
        except Exception:  # noqa: BLE001 — graceful degradation
            return ()
        return self.parse(pdf_to_text(pdf_bytes))

    def parse(self, body: str, *, default_year: int | None = None) -> tuple[PDDay, ...]:
        text = html_to_text(body) if "<" in body and ">" in body else body
        return extract_pd_days(
            text,
            default_year=default_year or current_academic_year_start(),
            source_label="Christ's Hospital",
        )

    @staticmethod
    def _pick_pdf_url(listing_html: str) -> str | None:
        """Pick the PDF whose start-year matches today's academic year.

        Falls back to the most-recent year when no exact match exists.
        """
        candidates: list[tuple[int, str]] = []
        for match in _PDF_LINK_RE.finditer(listing_html):
            href = match.group(1)
            year_match = re.search(r"(20\d{2})", href)
            year = int(year_match.group(1)) if year_match else 0
            absolute = urljoin(LISTING_URL, href)
            candidates.append((year, absolute))
        if not candidates:
            return None
        today_start = current_academic_year_start()
        for year, url_ in candidates:
            if year == today_start:
                return url_
        candidates.sort(reverse=True)
        return candidates[0][1]
