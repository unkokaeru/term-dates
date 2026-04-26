"""LEA-level term-date providers."""

from term_dates.lea.base import LEAProvider
from term_dates.lea.generic import GenericLEAProvider
from term_dates.lea.lincolnshire import LincolnshireProvider
from term_dates.lea.registry import (
    LEA_REGISTRY,
    all_leas,
    custom_count,
    custom_lea_names,
    find_lea,
    get_provider,
    has_custom_provider,
    implemented_count,
    implemented_lea_names,
    register_provider,
)

__all__ = [
    "LEA_REGISTRY",
    "GenericLEAProvider",
    "LEAProvider",
    "LincolnshireProvider",
    "all_leas",
    "custom_count",
    "custom_lea_names",
    "find_lea",
    "get_provider",
    "has_custom_provider",
    "implemented_count",
    "implemented_lea_names",
    "register_provider",
]
