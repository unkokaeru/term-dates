"""School directory backed by the GIAS "establishments" CSV extract.

The Department for Education publishes a daily CSV containing every
educational establishment in England (~27,000 rows, ~25MB):
    https://get-information-schools.service.gov.uk/Downloads

This module deliberately does not auto-download that file — it expects you to
either pass a path/URL explicitly or to use a smaller bundled dataset (such as
the one used in tests). That keeps the package light and avoids surprising
network calls.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path

from term_dates.http import Fetcher
from term_dates.models import LEA, School, SchoolPhase

# Mapping of GIAS "PhaseOfEducation" name -> our SchoolPhase enum.
_PHASE_MAP: dict[str, SchoolPhase] = {
    "Nursery": SchoolPhase.NURSERY,
    "Primary": SchoolPhase.PRIMARY,
    "Middle deemed primary": SchoolPhase.MIDDLE,
    "Middle deemed secondary": SchoolPhase.MIDDLE,
    "Secondary": SchoolPhase.SECONDARY,
    "16 plus": SchoolPhase.SIXTEEN_PLUS,
    "All-through": SchoolPhase.ALL_THROUGH,
    "All through": SchoolPhase.ALL_THROUGH,
}


@dataclass(slots=True)
class GIASSchoolDirectory:
    """In-memory directory of schools, indexed by LEA name."""

    schools: tuple[School, ...] = field(default_factory=tuple)

    @classmethod
    def from_csv_text(cls, text: str) -> GIASSchoolDirectory:
        return cls(schools=tuple(_iter_schools_from_csv_text(text)))

    @classmethod
    def from_csv_path(cls, path: str | Path) -> GIASSchoolDirectory:
        path = Path(path)
        return cls.from_csv_text(path.read_text(encoding="utf-8-sig"))

    @classmethod
    def from_url(cls, url: str, fetcher: Fetcher | None = None) -> GIASSchoolDirectory:
        f = fetcher or Fetcher.default()
        return cls.from_csv_text(f.get_text(url))

    # Query helpers -----------------------------------------------------

    def for_lea(self, lea: LEA | str) -> tuple[School, ...]:
        target = lea.name if isinstance(lea, LEA) else lea
        target_cf = target.casefold()
        return tuple(s for s in self.schools if s.lea_name.casefold() == target_cf)

    def search(
        self,
        *,
        lea: LEA | str | None = None,
        town: str | None = None,
        phase: SchoolPhase | None = None,
        name_contains: str | None = None,
    ) -> tuple[School, ...]:
        results: Iterable[School] = self.schools
        if lea is not None:
            target = lea.name if isinstance(lea, LEA) else lea
            lea_cf = target.casefold()
            results = (s for s in results if s.lea_name.casefold() == lea_cf)
        if town is not None:
            town_cf = town.casefold()
            results = (s for s in results if (s.town or "").casefold() == town_cf)
        if phase is not None:
            phase_target = phase
            results = (s for s in results if s.phase == phase_target)
        if name_contains is not None:
            name_cf = name_contains.casefold()
            results = (s for s in results if name_cf in s.name.casefold())
        return tuple(results)

    def __len__(self) -> int:
        return len(self.schools)


def load_schools_from_csv(path: str | Path) -> GIASSchoolDirectory:
    """Convenience factory used by the CLI and tests."""
    return GIASSchoolDirectory.from_csv_path(path)


def _iter_schools_from_csv_text(text: str) -> Iterable[School]:
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        urn = (row.get("URN") or "").strip()
        name = (row.get("EstablishmentName") or "").strip()
        if not urn or not name:
            continue
        # Skip closed schools — GIAS marks them via "EstablishmentStatus (name)".
        status = (row.get("EstablishmentStatus (name)") or "").strip().lower()
        if status and status not in {"open", "open, but proposed to close"}:
            continue
        yield School(
            urn=urn,
            name=name,
            lea_code=(row.get("LA (code)") or "").strip(),
            lea_name=(row.get("LA (name)") or "").strip(),
            phase=_PHASE_MAP.get(
                (row.get("PhaseOfEducation (name)") or "").strip(),
                SchoolPhase.OTHER,
            ),
            town=(row.get("Town") or "").strip() or None,
            postcode=(row.get("Postcode") or "").strip() or None,
            website=(row.get("SchoolWebsite") or "").strip() or None,
        )
