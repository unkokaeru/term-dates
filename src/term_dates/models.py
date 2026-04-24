"""Domain models for LEAs, schools, term dates, and PD days."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class EventKind(str, Enum):
    """The kind of date in a school calendar."""

    TERM_START = "term_start"
    TERM_END = "term_end"
    HALF_TERM_START = "half_term_start"
    HALF_TERM_END = "half_term_end"
    HOLIDAY_START = "holiday_start"
    HOLIDAY_END = "holiday_end"
    INSET = "inset"  # synonym for PD day at LEA-level
    BANK_HOLIDAY = "bank_holiday"


class SchoolPhase(str, Enum):
    NURSERY = "nursery"
    PRIMARY = "primary"
    MIDDLE = "middle"
    SECONDARY = "secondary"
    ALL_THROUGH = "all_through"
    SIXTEEN_PLUS = "16_plus"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class AcademicEvent:
    """A single dated event in an academic calendar."""

    date: date
    kind: EventKind
    label: str
    academic_year: str  # e.g. "2025/2026"


@dataclass(frozen=True, slots=True)
class TermDates:
    """All dated events published by an LEA for one or more academic years."""

    lea_code: str
    lea_name: str
    source_url: str
    events: tuple[AcademicEvent, ...]

    def for_year(self, academic_year: str) -> tuple[AcademicEvent, ...]:
        return tuple(e for e in self.events if e.academic_year == academic_year)

    def years(self) -> tuple[str, ...]:
        seen: dict[str, None] = {}
        for e in self.events:
            seen.setdefault(e.academic_year, None)
        return tuple(seen)


@dataclass(frozen=True, slots=True)
class LEA:
    """A Local Education Authority (English LA with maintained-school responsibility)."""

    code: str  # 3-digit DfE/GIAS code, e.g. "925" for Lincolnshire
    name: str  # canonical LA name, e.g. "Lincolnshire"
    region: str  # e.g. "East Midlands"
    term_dates_url: str | None = None


@dataclass(frozen=True, slots=True)
class School:
    """A maintained or independent school in England."""

    urn: str  # Unique Reference Number (GIAS)
    name: str
    lea_code: str
    lea_name: str
    phase: SchoolPhase
    town: str | None = None
    postcode: str | None = None
    website: str | None = None


@dataclass(frozen=True, slots=True)
class PDDay:
    """A school-specific professional-development / INSET day."""

    date: date
    label: str
    academic_year: str


@dataclass(slots=True)
class SchoolCalendar:
    """A school's calendar combining LEA-level events and school-specific PD days."""

    school: School
    lea_events: tuple[AcademicEvent, ...] = field(default_factory=tuple)
    pd_days: tuple[PDDay, ...] = field(default_factory=tuple)
    sources: tuple[str, ...] = field(default_factory=tuple)
