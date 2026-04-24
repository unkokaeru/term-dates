"""Registry of English LEAs and their term-dates providers.

Most LAs do not yet have a custom provider implementation in this package; the
registry still surfaces them (so the CLI drop-down lists every English LA), but
:func:`get_provider` returns ``None`` for them. Contributing a provider is just
adding a subclass of :class:`term_dates.lea.base.LEAProvider` and registering
it here.
"""

from __future__ import annotations

from collections.abc import Callable

from term_dates.lea._la_codes import LA_REFERENCE
from term_dates.lea.base import LEAProvider
from term_dates.lea.lincolnshire import LincolnshireProvider
from term_dates.models import LEA

# Build the canonical LEA tuple from reference data. Codes are populated by
# users from GIAS at runtime if needed (see term_dates.lea.codes).
LEA_REGISTRY: tuple[LEA, ...] = tuple(
    LEA(code="", name=name, region=region, term_dates_url=url)
    for name, region, url in LA_REFERENCE
)


# Provider classes keyed by LEA name. Add a row here when contributing a new
# provider. Keep keys aligned with LA_REFERENCE names.
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
    """Return an instantiated provider for the LEA, or None if unimplemented."""
    cls = _PROVIDER_BY_NAME.get(lea.name)
    if cls is None:
        return None
    return cls(**provider_kwargs)  # type: ignore[arg-type]


def register_provider(name: str, provider_cls: type[LEAProvider]) -> None:
    """Register an additional provider at runtime (useful for plugins)."""
    _PROVIDER_BY_NAME[name] = provider_cls


def implemented_lea_names() -> tuple[str, ...]:
    """Names of LEAs that currently have a custom provider implementation."""
    return tuple(sorted(_PROVIDER_BY_NAME))


def implemented_count() -> int:
    return len(_PROVIDER_BY_NAME)


# Convenience iterator for downstream tools that want a callable factory map.
def provider_factories() -> dict[str, Callable[[], LEAProvider]]:
    return {name: cls for name, cls in _PROVIDER_BY_NAME.items()}
