"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def lincolnshire_html() -> str:
    return (FIXTURES / "lincolnshire_term_times.html").read_text(encoding="utf-8")


@pytest.fixture
def priory_html() -> str:
    return (FIXTURES / "priory_city_of_lincoln_term_dates.html").read_text(encoding="utf-8")


@pytest.fixture
def christs_hospital_html() -> str:
    return (FIXTURES / "lincoln_christs_hospital_term_dates.html").read_text(encoding="utf-8")


@pytest.fixture
def carlton_html() -> str:
    return (FIXTURES / "lincoln_carlton_term_dates.html").read_text(encoding="utf-8")


@pytest.fixture
def gias_lincoln_csv() -> Path:
    return FIXTURES / "gias_lincoln_sample.csv"
