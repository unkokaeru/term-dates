"""Abstract base class for school-specific PD-day providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from term_dates.http import Fetcher
from term_dates.models import PDDay, School


class PDDayProvider(ABC):
    """Fetches PD/INSET days published on a single school's website."""

    school: School
    source_url: str

    def __init__(self, fetcher: Fetcher | None = None) -> None:
        self.fetcher = fetcher or Fetcher.default()

    @abstractmethod
    def fetch(self) -> tuple[PDDay, ...]:
        """Download and parse this school's PD-day calendar."""

    def parse(self, html: str) -> tuple[PDDay, ...]:
        """Parse already-fetched HTML — providers should override for testing."""
        raise NotImplementedError(
            f"{type(self).__name__} does not implement offline parse()"
        )
