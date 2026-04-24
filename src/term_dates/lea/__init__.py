"""LEA-level term-date providers."""

from term_dates.lea.base import LEAProvider
from term_dates.lea.lincolnshire import LincolnshireProvider
from term_dates.lea.registry import (
    LEA_REGISTRY,
    all_leas,
    find_lea,
    get_provider,
    implemented_count,
    implemented_lea_names,
    register_provider,
)

__all__ = [
    "LEA_REGISTRY",
    "LEAProvider",
    "LincolnshireProvider",
    "all_leas",
    "find_lea",
    "get_provider",
    "implemented_count",
    "implemented_lea_names",
    "register_provider",
]
