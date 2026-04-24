"""PD-day provider for Lincoln Carlton Academy (URN 142037)."""

from __future__ import annotations

from term_dates.models import PDDay, School, SchoolPhase
from term_dates.schools._extract import extract_pd_days, html_to_text
from term_dates.schools.base import PDDayProvider

URL = "https://www.lincolncarlton.anthemtrust.uk/term-dates-and-school-times"


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
        return self.parse(html)

    def parse(self, html: str) -> tuple[PDDay, ...]:
        return extract_pd_days(
            html_to_text(html),
            default_year=2025,
            source_label="Lincoln Carlton",
        )
