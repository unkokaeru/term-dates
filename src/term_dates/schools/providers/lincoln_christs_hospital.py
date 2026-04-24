"""PD-day provider for Lincoln Christ's Hospital School (URN 120636)."""

from __future__ import annotations

from term_dates.models import PDDay, School, SchoolPhase
from term_dates.schools._extract import extract_pd_days, html_to_text
from term_dates.schools.base import PDDayProvider

# The school publishes term dates as a PDF, but mirrors the same content on
# its News pages. We point at the HTML term-dates page; the parse() method
# accepts either HTML or pre-extracted text, so callers with a PDF can pass
# the extracted text directly.
URL = "https://lincolnchristshospitalschool.co.uk/about-us/term-dates/"


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
    source_url = URL

    def fetch(self) -> tuple[PDDay, ...]:
        body = self.fetcher.get_text(URL)
        return self.parse(body)

    def parse(self, body: str) -> tuple[PDDay, ...]:
        # Heuristic: treat anything that contains an HTML tag as HTML.
        text = html_to_text(body) if "<" in body and ">" in body else body
        return extract_pd_days(
            text,
            default_year=2025,
            source_label="Christ's Hospital",
        )
