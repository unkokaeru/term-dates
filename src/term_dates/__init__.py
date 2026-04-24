"""Aggregate LEA term dates across England, with optional per-school PD-day polling."""

from term_dates.models import (
    LEA,
    AcademicEvent,
    EventKind,
    PDDay,
    School,
    SchoolPhase,
    TermDates,
)

__all__ = [
    "AcademicEvent",
    "EventKind",
    "LEA",
    "PDDay",
    "School",
    "SchoolPhase",
    "TermDates",
]

__version__ = "0.1.0"
