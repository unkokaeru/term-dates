"""Test City of Lincoln school PD-day providers against fixture pages."""

from __future__ import annotations

from datetime import date

from term_dates.schools.providers.lincoln_carlton import LincolnCarltonProvider
from term_dates.schools.providers.lincoln_christs_hospital import (
    LincolnChristsHospitalProvider,
)
from term_dates.schools.providers.priory_city_of_lincoln import (
    PrioryCityOfLincolnProvider,
)

# ---- The Priory City of Lincoln Academy --------------------------------

def test_priory_pd_days_extracted(priory_html: str) -> None:
    provider = PrioryCityOfLincolnProvider()
    days = provider.parse(priory_html)
    dates = {d.date for d in days}
    assert date(2025, 9, 1) in dates
    assert date(2025, 9, 2) in dates
    assert date(2026, 1, 5) in dates
    assert date(2026, 6, 26) in dates
    assert date(2026, 7, 20) in dates
    # No school days should leak in.
    assert date(2025, 9, 3) not in dates  # term begins (students)


def test_priory_pd_days_have_correct_academic_year(priory_html: str) -> None:
    days = PrioryCityOfLincolnProvider().parse(priory_html)
    for d in days:
        assert d.academic_year == "2025/2026"


# ---- Lincoln Christ's Hospital School ----------------------------------

def test_christs_hospital_pd_days(christs_hospital_html: str) -> None:
    days = LincolnChristsHospitalProvider().parse(christs_hospital_html)
    dates = {d.date for d in days}
    assert date(2025, 9, 1) in dates  # INSET
    assert date(2026, 2, 13) in dates  # INSET
    assert date(2026, 7, 6) in dates  # INSET
    assert date(2026, 7, 27) in dates  # Professional Development Day
    # Pupil days should not be flagged as PD.
    assert date(2025, 9, 2) not in dates


# ---- Lincoln Carlton Academy -------------------------------------------

def test_lincoln_carlton_pd_days(carlton_html: str) -> None:
    days = LincolnCarltonProvider().parse(carlton_html)
    dates = {d.date for d in days}
    assert date(2025, 9, 1) in dates  # Training day
    assert date(2025, 9, 2) in dates  # Training day
    assert date(2026, 2, 13) in dates  # Inset day
    assert date(2026, 6, 26) in dates  # Non-pupil day


# ---- Provider metadata is consistent with City of Lincoln context ------

def test_all_lincoln_providers_in_lincolnshire() -> None:
    for cls in (
        PrioryCityOfLincolnProvider,
        LincolnChristsHospitalProvider,
        LincolnCarltonProvider,
    ):
        assert cls.school.lea_name == "Lincolnshire"
        assert cls.school.town == "Lincoln"
        assert cls.school.urn  # non-empty URN
        assert cls.source_url.startswith("https://")
