from datetime import date

from term_dates.parsing import (
    academic_year_for,
    looks_like_pd_day,
    parse_uk_date,
    parse_uk_date_range,
)


def test_parse_uk_date_simple() -> None:
    assert parse_uk_date("Monday 8 September 2025") == date(2025, 9, 8)
    assert parse_uk_date("8 Sep 2025") == date(2025, 9, 8)
    assert parse_uk_date("8/9/2025") == date(2025, 9, 8)


def test_parse_uk_date_invalid() -> None:
    assert parse_uk_date("not a date") is None
    assert parse_uk_date("") is None


def test_parse_uk_date_range_with_year_only_on_end() -> None:
    rng = parse_uk_date_range("Mon 27 October to Fri 31 October 2025")
    assert rng == (date(2025, 10, 27), date(2025, 10, 31))


def test_parse_uk_date_range_dash() -> None:
    rng = parse_uk_date_range("Wed 3 September 2025 – Fri 19 December 2025")
    assert rng == (date(2025, 9, 3), date(2025, 12, 19))


def test_academic_year_boundary() -> None:
    assert academic_year_for(date(2025, 8, 31)) == "2024/2025"
    assert academic_year_for(date(2025, 9, 1)) == "2025/2026"
    assert academic_year_for(date(2026, 4, 24)) == "2025/2026"


def test_looks_like_pd_day_vocabulary() -> None:
    for label in [
        "INSET day",
        "PD day",
        "Professional Development Day",
        "Training day",
        "Staff training",
        "Non-pupil day",
        "Occasional day",
        "Teacher training",
    ]:
        assert looks_like_pd_day(label), f"expected {label!r} to match"


def test_looks_like_pd_day_negative() -> None:
    assert not looks_like_pd_day("Term starts")
    assert not looks_like_pd_day("Half term")
    assert not looks_like_pd_day("Bank holiday")
