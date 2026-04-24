"""Registry of school-specific PD-day providers."""

from __future__ import annotations

from term_dates.schools.base import PDDayProvider
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


def get_pd_provider(urn: str, **provider_kwargs: object) -> PDDayProvider | None:
    cls = SCHOOL_PD_PROVIDERS.get(urn)
    if cls is None:
        return None
    return cls(**provider_kwargs)  # type: ignore[arg-type]


def register_pd_provider(urn: str, provider_cls: type[PDDayProvider]) -> None:
    SCHOOL_PD_PROVIDERS[urn] = provider_cls


def pd_providers_for_lea(lea_name: str) -> dict[str, type[PDDayProvider]]:
    """Return PD providers whose school sits in the given LEA."""
    target = lea_name.casefold()
    return {
        urn: cls
        for urn, cls in SCHOOL_PD_PROVIDERS.items()
        if cls.school.lea_name.casefold() == target
    }
