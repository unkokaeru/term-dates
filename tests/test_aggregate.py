"""End-to-end test: pick City of Lincoln schools, aggregate their PD days."""

from __future__ import annotations

from datetime import date

from term_dates.models import SchoolPhase
from term_dates.schools.gias import GIASSchoolDirectory
from term_dates.schools.registry import (
    SCHOOL_PD_PROVIDERS,
    pd_providers_for_lea,
)


def test_lincoln_schools_filtered_from_directory(gias_lincoln_csv) -> None:  # type: ignore[no-untyped-def]
    directory = GIASSchoolDirectory.from_csv_path(gias_lincoln_csv)
    lincoln_schools = directory.search(lea="Lincolnshire", town="Lincoln")
    assert {s.urn for s in lincoln_schools} >= {"137178", "120636", "142037"}


def test_pd_providers_for_lincolnshire_include_three_lincoln_schools() -> None:
    providers = pd_providers_for_lea("Lincolnshire")
    urns = set(providers)
    assert {"137178", "120636", "142037"} <= urns


def _parse_with_fixture(cls, html: str):  # type: ignore[no-untyped-def]
    return cls().parse(html)


def test_aggregate_lincoln_pd_days_across_three_schools(
    priory_html: str,
    christs_hospital_html: str,
    carlton_html: str,
) -> None:
    """Populate City of Lincoln school PD days, aggregated.

    This is the worked example called out in the project brief: combine PD days
    from every school in the City of Lincoln that has a registered provider,
    and verify the merged set spans the expected dates.
    """
    from term_dates.schools.providers.lincoln_carlton import LincolnCarltonProvider
    from term_dates.schools.providers.lincoln_christs_hospital import (
        LincolnChristsHospitalProvider,
    )
    from term_dates.schools.providers.priory_city_of_lincoln import (
        PrioryCityOfLincolnProvider,
    )

    aggregated: dict[str, set] = {}
    for cls, html in (
        (PrioryCityOfLincolnProvider, priory_html),
        (LincolnChristsHospitalProvider, christs_hospital_html),
        (LincolnCarltonProvider, carlton_html),
    ):
        days = cls().parse(html)
        aggregated[cls.school.name] = {d.date for d in days}

    # Every school had at least one PD day on or near 1 September 2025.
    september_starts = {
        name: any(d.year == 2025 and d.month == 9 for d in dates)
        for name, dates in aggregated.items()
    }
    assert all(september_starts.values()), september_starts

    # Combined set covers a representative spread across the year.
    combined: set = set().union(*aggregated.values())
    assert date(2025, 9, 1) in combined
    assert date(2026, 2, 13) in combined  # spring INSET
    assert any(d.month in {6, 7} and d.year == 2026 for d in combined)


def test_full_aggregated_pd_day_summary(
    priory_html: str,
    christs_hospital_html: str,
    carlton_html: str,
) -> None:
    """Print-style assertion: each school contributes a non-trivial number of PDs."""
    from term_dates.schools.providers.lincoln_carlton import LincolnCarltonProvider
    from term_dates.schools.providers.lincoln_christs_hospital import (
        LincolnChristsHospitalProvider,
    )
    from term_dates.schools.providers.priory_city_of_lincoln import (
        PrioryCityOfLincolnProvider,
    )

    counts = {
        "Priory City of Lincoln": len(PrioryCityOfLincolnProvider().parse(priory_html)),
        "Christ's Hospital": len(LincolnChristsHospitalProvider().parse(christs_hospital_html)),
        "Lincoln Carlton": len(LincolnCarltonProvider().parse(carlton_html)),
    }
    for school, n in counts.items():
        assert n >= 3, f"{school} produced only {n} PD days"


def test_registry_keys_match_school_urns() -> None:
    for urn, cls in SCHOOL_PD_PROVIDERS.items():
        assert urn == cls.school.urn


def test_phase_for_lincoln_schools() -> None:
    """Sanity: providers cover both primary and secondary phases."""
    phases = {cls.school.phase for cls in SCHOOL_PD_PROVIDERS.values()}
    assert SchoolPhase.SECONDARY in phases
    assert SchoolPhase.PRIMARY in phases
