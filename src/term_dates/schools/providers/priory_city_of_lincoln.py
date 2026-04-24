"""PD-day provider for The Priory City of Lincoln Academy (URN 137178)."""

from __future__ import annotations

from term_dates.models import PDDay, School, SchoolPhase
from term_dates.schools._extract import extract_pd_days, html_to_text
from term_dates.schools.base import PDDayProvider

URL = "https://www.priorycity.co.uk/page/?title=TERM+DATES+2025-2026&pid=296"


class PrioryCityOfLincolnProvider(PDDayProvider):
    """Scrapes PD/INSET dates from the Priory City of Lincoln Academy site."""

    school = School(
        urn="137178",
        name="The Priory City of Lincoln Academy",
        lea_code="925",
        lea_name="Lincolnshire",
        phase=SchoolPhase.SECONDARY,
        town="Lincoln",
        postcode="LN6 7AS",
        website="https://www.priorycity.co.uk/",
    )
    source_url = URL

    def fetch(self) -> tuple[PDDay, ...]:
        html = self.fetcher.get_text(URL)
        return self.parse(html)

    def parse(self, html: str) -> tuple[PDDay, ...]:
        return extract_pd_days(
            html_to_text(html),
            default_year=2025,
            source_label="Priory City",
        )
