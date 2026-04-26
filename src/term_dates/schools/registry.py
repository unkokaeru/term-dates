"""Registry of school-specific PD-day providers.

Two tiers:

* ``SCHOOL_PD_PROVIDERS`` maps GIAS URN → curated provider class. Add a row
  here when contributing a hand-rolled scraper for a specific school.
* :class:`GenericSchoolPDProvider` auto-fills any other school whose
  :class:`School.website` is set, by probing common term-date URL paths.
"""

from __future__ import annotations

from term_dates.models import School
from term_dates.schools.base import PDDayProvider
from term_dates.schools.generic import GenericSchoolPDProvider
from term_dates.schools.providers.lincoln_carlton import LincolnCarltonProvider
from term_dates.schools.providers.lincoln_christs_hospital import (
    LincolnChristsHospitalProvider,
)
from term_dates.schools.providers.priory_city_of_lincoln import (
    PrioryCityOfLincolnProvider,
)

# Keyed by GIAS URN — the only stable identifier for English schools.
SCHOOL_PD_PROVIDERS: dict[str, type[PDDayProvider]] = {
    PrioryCityOfLincolnProvider.school.urn: PrioryCityOfLincolnProvider,
    LincolnChristsHospitalProvider.school.urn: LincolnChristsHospitalProvider,
    LincolnCarltonProvider.school.urn: LincolnCarltonProvider,
}


def get_pd_provider(
    urn: str,
    *,
    school: School | None = None,
    **provider_kwargs: object,
) -> PDDayProvider | None:
    """Return a PD-day provider for the school.

    Resolves curated providers first; falls back to a generic best-effort
    one when ``school`` is supplied and has a website. Returns ``None`` if
    nothing useful can be constructed.
    """
    cls = SCHOOL_PD_PROVIDERS.get(urn)
    if cls is not None:
        return cls(**provider_kwargs)  # type: ignore[arg-type]
    if school is not None and school.website:
        return GenericSchoolPDProvider(school, **provider_kwargs)  # type: ignore[arg-type]
    return None


def register_pd_provider(urn: str, provider_cls: type[PDDayProvider]) -> None:
    SCHOOL_PD_PROVIDERS[urn] = provider_cls


def has_curated_pd_provider(urn: str) -> bool:
    return urn in SCHOOL_PD_PROVIDERS


def pd_providers_for_lea(lea_name: str) -> dict[str, type[PDDayProvider]]:
    """Return curated PD providers whose school sits in the given LEA."""
    target = lea_name.casefold()
    return {
        urn: cls
        for urn, cls in SCHOOL_PD_PROVIDERS.items()
        if cls.school.lea_name.casefold() == target
    }
