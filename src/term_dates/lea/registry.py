"""Registry of English LEAs and their term-dates providers.

Two tiers of provider exist:

* **Custom providers** are bespoke parser classes registered in
  ``_PROVIDER_BY_NAME`` (currently: Lincolnshire). They have hand-written
  HTML / table logic for that council's specific page shape.
* **Generic providers** auto-fill every other LEA that publishes a
  ``term_dates_url``. :func:`get_provider` returns
  :class:`GenericLEAProvider` for these — best-effort, sometimes empty.

Use :func:`custom_lea_names` to list curated providers and
:func:`implemented_lea_names` for "anything we can fetch" (custom + generic).
"""

from __future__ import annotations

from collections.abc import Callable

from term_dates.lea._la_codes import LA_REFERENCE
from term_dates.lea.base import LEAProvider
from term_dates.lea.generic import GenericLEAProvider
from term_dates.lea.lincolnshire import LincolnshireProvider
from term_dates.models import LEA

# Build the canonical LEA tuple from reference data. Codes are populated by
# users from GIAS at runtime if needed.
LEA_REGISTRY: tuple[LEA, ...] = tuple(
    LEA(code="", name=name, region=region, term_dates_url=url)
    for name, region, url in LA_REFERENCE
)


# Custom provider classes keyed by LEA name. Add a row here when contributing
# a hand-rolled parser for a specific council.
_PROVIDER_BY_NAME: dict[str, type[LEAProvider]] = {
    "Lincolnshire": LincolnshireProvider,
}


def all_leas() -> tuple[LEA, ...]:
    """All English LEAs in the registry, sorted by name."""
    return tuple(sorted(LEA_REGISTRY, key=lambda lea: lea.name))


def find_lea(name: str) -> LEA | None:
    """Lookup an LEA by case-insensitive name match."""
    target = name.strip().casefold()
    for lea in LEA_REGISTRY:
        if lea.name.casefold() == target:
            return lea
    return None


def get_provider(lea: LEA, **provider_kwargs: object) -> LEAProvider | None:
    """Return an instantiated provider for the LEA.

    Resolution order: custom curated provider, then a best-effort
    :class:`GenericLEAProvider` whenever the LEA has a published URL.
    Returns ``None`` only if the LEA has neither.
    """
    cls = _PROVIDER_BY_NAME.get(lea.name)
    if cls is not None:
        return cls(**provider_kwargs)  # type: ignore[arg-type]
    if lea.term_dates_url:
        return GenericLEAProvider(lea, **provider_kwargs)  # type: ignore[arg-type]
    return None


def has_custom_provider(name: str) -> bool:
    return name in _PROVIDER_BY_NAME


def register_provider(name: str, provider_cls: type[LEAProvider]) -> None:
    """Register an additional curated provider at runtime."""
    _PROVIDER_BY_NAME[name] = provider_cls


def custom_lea_names() -> tuple[str, ...]:
    """Names of LEAs that have a curated custom provider."""
    return tuple(sorted(_PROVIDER_BY_NAME))


def implemented_lea_names() -> tuple[str, ...]:
    """Names of LEAs we can fetch — either custom or generic-with-URL."""
    names = set(_PROVIDER_BY_NAME)
    names.update(lea.name for lea in LEA_REGISTRY if lea.term_dates_url)
    return tuple(sorted(names))


def implemented_count() -> int:
    return len(implemented_lea_names())


def custom_count() -> int:
    return len(_PROVIDER_BY_NAME)


def provider_factories() -> dict[str, Callable[[], LEAProvider]]:
    """Curated providers only. Generic providers are constructed on demand."""
    return dict(_PROVIDER_BY_NAME.items())
