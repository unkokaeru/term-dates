"""High-level aggregation API: pull term dates for many LEAs at once."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from term_dates.http import Fetcher
from term_dates.lea import LEAProvider, all_leas, get_provider
from term_dates.models import LEA, AcademicEvent, PDDay, School, SchoolCalendar, TermDates
from term_dates.schools import get_pd_provider
from term_dates.schools.gias import GIASSchoolDirectory


@dataclass(slots=True)
class AggregateResult:
    """Result of aggregating LEA term dates across England."""

    successes: dict[str, TermDates] = field(default_factory=dict)
    skipped: tuple[str, ...] = ()  # LEAs without a provider yet
    failures: dict[str, str] = field(default_factory=dict)  # name -> error message

    @property
    def covered_lea_count(self) -> int:
        return len(self.successes)

    @property
    def total_lea_count(self) -> int:
        return self.covered_lea_count + len(self.skipped) + len(self.failures)


def aggregate_all_leas(
    *,
    fetcher: Fetcher | None = None,
    max_workers: int = 8,
    only: tuple[str, ...] | None = None,
) -> AggregateResult:
    """Fetch term dates for every LEA that has a registered provider.

    LEAs without a provider yet are reported in ``result.skipped`` rather than
    failing — they will simply need their own provider written.
    """
    fetcher = fetcher or Fetcher.default()
    leas = all_leas()
    if only is not None:
        wanted = {n.casefold() for n in only}
        leas = tuple(lea for lea in leas if lea.name.casefold() in wanted)

    succ: dict[str, TermDates] = {}
    skipped: list[str] = []
    failures: dict[str, str] = {}

    runnable: list[tuple[LEA, LEAProvider]] = []
    for lea in leas:
        provider = get_provider(lea, fetcher=fetcher)
        if provider is None:
            skipped.append(lea.name)
        else:
            runnable.append((lea, provider))

    if runnable:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_name = {
                pool.submit(provider.fetch): lea.name for lea, provider in runnable
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    succ[name] = future.result()
                except Exception as exc:  # noqa: BLE001 — provider errors are expected
                    failures[name] = f"{type(exc).__name__}: {exc}"

    return AggregateResult(
        successes=succ, skipped=tuple(sorted(skipped)), failures=failures
    )


def build_school_calendar(
    school: School,
    *,
    fetcher: Fetcher | None = None,
) -> SchoolCalendar:
    """Combine a school's LEA term dates with school-specific PD days."""
    fetcher = fetcher or Fetcher.default()

    lea_events: tuple[AcademicEvent, ...] = ()
    sources: list[str] = []

    # LEA-level events ---------------------------------------------------
    lea = LEA(code=school.lea_code, name=school.lea_name, region="")
    provider = get_provider(lea, fetcher=fetcher)
    if provider is not None:
        try:
            lea_dates = provider.fetch()
            lea_events = lea_dates.events
            sources.append(lea_dates.source_url)
        except Exception:  # noqa: BLE001 — keep best-effort behaviour
            pass

    # School-specific PD days --------------------------------------------
    pd_days: tuple[PDDay, ...] = ()
    pd_provider = get_pd_provider(school.urn, school=school, fetcher=fetcher)
    if pd_provider is not None:
        try:
            pd_days = pd_provider.fetch()
            sources.append(pd_provider.source_url)
        except Exception:  # noqa: BLE001
            pass

    return SchoolCalendar(
        school=school,
        lea_events=lea_events,
        pd_days=pd_days,
        sources=tuple(sources),
    )


def schools_in_town(
    directory: GIASSchoolDirectory, *, lea_name: str, town: str
) -> tuple[School, ...]:
    """Filter a GIAS directory down to schools in a particular town within an LEA."""
    return directory.search(lea=lea_name, town=town)
