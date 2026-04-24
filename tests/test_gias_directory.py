"""Test the GIAS-backed school directory."""

from __future__ import annotations

from term_dates.models import SchoolPhase
from term_dates.schools.gias import GIASSchoolDirectory


def test_loads_csv(gias_lincoln_csv) -> None:  # type: ignore[no-untyped-def]
    directory = GIASSchoolDirectory.from_csv_path(gias_lincoln_csv)
    # Closed school should be filtered out.
    urns = {s.urn for s in directory.schools}
    assert "137178" in urns  # Priory City of Lincoln Academy
    assert "120636" in urns
    # Sanity: the only "Closed" row was URN 120565 with name "Closed Example".
    assert not any(s.name == "Closed Example" for s in directory.schools)


def test_filter_by_lea_and_town(gias_lincoln_csv) -> None:  # type: ignore[no-untyped-def]
    directory = GIASSchoolDirectory.from_csv_path(gias_lincoln_csv)
    lincs_lincoln = directory.search(lea="Lincolnshire", town="Lincoln")
    names = {s.name for s in lincs_lincoln}
    assert "The Priory City of Lincoln Academy" in names
    assert "Lincoln Carlton Academy" in names
    assert "Boston Grammar School" not in names  # different town


def test_filter_by_phase(gias_lincoln_csv) -> None:  # type: ignore[no-untyped-def]
    directory = GIASSchoolDirectory.from_csv_path(gias_lincoln_csv)
    primaries = directory.search(lea="Lincolnshire", phase=SchoolPhase.PRIMARY)
    assert all(s.phase == SchoolPhase.PRIMARY for s in primaries)
    assert any(s.name == "Lincoln Carlton Academy" for s in primaries)


def test_for_lea_returns_only_lincolnshire(gias_lincoln_csv) -> None:  # type: ignore[no-untyped-def]
    directory = GIASSchoolDirectory.from_csv_path(gias_lincoln_csv)
    schools = directory.for_lea("Lincolnshire")
    assert len(schools) >= 6
    assert all(s.lea_name == "Lincolnshire" for s in schools)
