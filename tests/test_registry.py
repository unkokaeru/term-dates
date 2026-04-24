"""Test the LEA registry covers all English LAs and resolves providers."""

from __future__ import annotations

from term_dates.lea import (
    all_leas,
    find_lea,
    get_provider,
    implemented_count,
    implemented_lea_names,
)
from term_dates.lea.lincolnshire import LincolnshireProvider


def test_registry_has_substantial_coverage() -> None:
    leas = all_leas()
    # 152 English LAs is the official figure; allow modest slack for renames.
    assert len(leas) >= 145
    # All LEA names unique.
    names = [lea.name for lea in leas]
    assert len(set(names)) == len(names)


def test_each_lea_has_region_and_url() -> None:
    for lea in all_leas():
        assert lea.region, f"missing region for {lea.name}"
        # URLs are best-effort but every entry should have one.
        assert lea.term_dates_url, f"missing URL for {lea.name}"


def test_find_lea_case_insensitive() -> None:
    assert find_lea("Lincolnshire") is not None
    assert find_lea("lincolnshire") is not None
    assert find_lea("LINCOLNSHIRE") is not None
    assert find_lea("Atlantis") is None


def test_lincolnshire_provider_resolves() -> None:
    lea = find_lea("Lincolnshire")
    assert lea is not None
    provider = get_provider(lea)
    assert isinstance(provider, LincolnshireProvider)


def test_unknown_provider_returns_none() -> None:
    lea = find_lea("Westminster")
    assert lea is not None
    assert get_provider(lea) is None


def test_implemented_lea_names() -> None:
    names = implemented_lea_names()
    assert "Lincolnshire" in names
    assert implemented_count() == len(names)
