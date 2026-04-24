"""Abstract base class for LEA term-date providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from term_dates.http import Fetcher
from term_dates.models import LEA, TermDates


class LEAProvider(ABC):
    """Fetches and parses the term-dates page for one Local Education Authority."""

    lea: LEA

    def __init__(self, fetcher: Fetcher | None = None) -> None:
        self.fetcher = fetcher or Fetcher.default()

    @abstractmethod
    def fetch(self) -> TermDates:
        """Download and parse this LEA's published term dates."""

    def parse(self, html: str, *, source_url: str | None = None) -> TermDates:
        """Parse already-fetched HTML. Override when convenient for testing.

        The default implementation raises; providers that want fixture-based
        testing should override this method.
        """
        raise NotImplementedError(
            f"{type(self).__name__} does not implement offline parse()"
        )
