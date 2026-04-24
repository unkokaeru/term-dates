"""Command-line interface for the term-dates package."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import questionary
import typer
from rich.console import Console
from rich.table import Table

from term_dates.aggregate import (
    AggregateResult,
    aggregate_all_leas,
    build_school_calendar,
)
from term_dates.http import Fetcher
from term_dates.lea import all_leas, find_lea, implemented_lea_names
from term_dates.models import LEA, School, SchoolCalendar
from term_dates.schools.gias import GIASSchoolDirectory
from term_dates.schools.registry import SCHOOL_PD_PROVIDERS, pd_providers_for_lea

app = typer.Typer(
    add_completion=False,
    help="Aggregate LEA term dates across England, with optional per-school PD days.",
)
console = Console()


# ---- helpers ----------------------------------------------------------

def _load_directory(csv_path: Path | None) -> GIASSchoolDirectory:
    """Load the school directory from a GIAS CSV, or fall back to bundled providers."""
    if csv_path is not None:
        return GIASSchoolDirectory.from_csv_path(csv_path)
    # Fallback: synthesise a tiny directory from the schools registered with
    # PD-day providers, so the CLI works out-of-the-box without GIAS data.
    schools = tuple(cls.school for cls in SCHOOL_PD_PROVIDERS.values())
    return GIASSchoolDirectory(schools=schools)


def _print_aggregate(result: AggregateResult) -> None:
    table = Table(title="LEA term-dates aggregation", show_lines=False)
    table.add_column("LEA", style="bold")
    table.add_column("Events")
    table.add_column("Years")
    table.add_column("Source")
    for name, td in sorted(result.successes.items()):
        table.add_row(
            name,
            str(len(td.events)),
            ", ".join(td.years()) or "-",
            td.source_url,
        )
    console.print(table)
    if result.skipped:
        console.print(
            f"[yellow]Skipped[/yellow] (no provider yet): {len(result.skipped)} LEAs."
            f"  e.g. {', '.join(result.skipped[:5])}…"
        )
    if result.failures:
        console.print("[red]Failures:[/red]")
        for name, msg in result.failures.items():
            console.print(f"  - {name}: {msg}")


def _print_school_calendar(cal: SchoolCalendar) -> None:
    console.rule(f"[bold]{cal.school.name}[/bold]  ({cal.school.lea_name}, URN {cal.school.urn})")
    if cal.lea_events:
        t = Table(title="LEA term/holiday/inset events")
        t.add_column("Date")
        t.add_column("Kind")
        t.add_column("Year")
        t.add_column("Label")
        for e in sorted(cal.lea_events, key=lambda e: e.date):
            t.add_row(e.date.isoformat(), e.kind.value, e.academic_year, e.label)
        console.print(t)
    else:
        console.print(
            "[dim]No LEA-level events available "
            "(provider not implemented or fetch failed).[/dim]"
        )

    if cal.pd_days:
        t = Table(title="School-specific PD / INSET days")
        t.add_column("Date")
        t.add_column("Year")
        t.add_column("Label")
        for p in sorted(cal.pd_days, key=lambda p: p.date):
            t.add_row(p.date.isoformat(), p.academic_year, p.label)
        console.print(t)
    else:
        console.print(
            "[dim]No PD days found (no provider for this school, or page unreachable).[/dim]"
        )

    if cal.sources:
        console.print("[dim]Sources:[/dim] " + ", ".join(cal.sources))


# ---- commands ---------------------------------------------------------

@app.command("list-leas")
def list_leas(
    implemented_only: bool = typer.Option(
        False, "--implemented-only", help="Only list LEAs with a provider"
    ),
) -> None:
    """List every English LEA the registry knows about."""
    leas: Iterable[LEA] = all_leas()
    if implemented_only:
        names = set(implemented_lea_names())
        leas = (lea for lea in leas if lea.name in names)
    table = Table(title="English Local Education Authorities")
    table.add_column("Name", style="bold")
    table.add_column("Region")
    table.add_column("Provider?")
    table.add_column("URL")
    impl = set(implemented_lea_names())
    count = 0
    for lea in leas:
        table.add_row(
            lea.name,
            lea.region,
            "[green]yes[/green]" if lea.name in impl else "-",
            lea.term_dates_url or "",
        )
        count += 1
    console.print(table)
    console.print(f"[dim]Total: {count} LEAs ({len(impl)} with providers).[/dim]")


@app.command("aggregate")
def aggregate(
    only: list[str] | None = typer.Option(  # noqa: B008
        None, "--lea", help="Limit to one or more LEA names (repeatable)."
    ),
    workers: int = typer.Option(8, help="Concurrent fetches."),
) -> None:
    """Aggregate term dates from every LEA that has a provider."""
    fetcher = Fetcher.default()
    result = aggregate_all_leas(
        fetcher=fetcher,
        max_workers=workers,
        only=tuple(only) if only else None,
    )
    _print_aggregate(result)


@app.command("school")
def school(
    lea_name: str | None = typer.Option(None, "--lea", help="Pre-select an LEA by name."),
    school_urn: str | None = typer.Option(None, "--urn", help="Pre-select a school by URN."),
    gias_csv: Path | None = typer.Option(
        None,
        "--gias-csv",
        help="Path to a GIAS establishments CSV to power the school list.",
        exists=True,
        readable=True,
    ),
) -> None:
    """Interactively pick an LEA + school and print its calendar with PD days."""
    directory = _load_directory(gias_csv)

    # Pick LEA (drop-down if not provided) ------------------------------
    if lea_name:
        lea = find_lea(lea_name)
        if lea is None:
            console.print(f"[red]Unknown LEA:[/red] {lea_name}")
            raise typer.Exit(2)
    else:
        choices = [lea.name for lea in all_leas()]
        choice = questionary.select("Choose an LEA:", choices=choices).ask()
        if not choice:
            raise typer.Exit(1)
        lea = find_lea(choice)
        assert lea is not None

    # Pick school (drop-down) -------------------------------------------
    schools = directory.for_lea(lea)
    if not schools:
        console.print(
            f"[yellow]No schools known for {lea.name}.[/yellow] "
            "Pass --gias-csv to load the full GIAS extract, or rely on the bundled "
            "small registry."
        )
        raise typer.Exit(1)

    if school_urn:
        match = next((s for s in schools if s.urn == school_urn), None)
        if match is None:
            console.print(f"[red]URN {school_urn} not found in {lea.name}.[/red]")
            raise typer.Exit(2)
        chosen_school = match
    else:
        labels = {f"{s.name}  ({s.town or 'Unknown'} — URN {s.urn})": s for s in schools}
        choice = questionary.select(f"Schools in {lea.name}:", choices=list(labels)).ask()
        if not choice:
            raise typer.Exit(1)
        chosen_school = labels[choice]

    cal = build_school_calendar(chosen_school)
    _print_school_calendar(cal)


@app.command("schools-in-lea")
def schools_in_lea(
    lea_name: str = typer.Argument(..., help="LEA name, e.g. 'Lincolnshire'"),
    town: str | None = typer.Option(None, help="Filter by town, e.g. 'Lincoln'"),
    gias_csv: Path | None = typer.Option(
        None, "--gias-csv", exists=True, readable=True,
        help="Path to a GIAS establishments CSV.",
    ),
) -> None:
    """Print all schools known for an LEA (optionally filtered by town)."""
    directory = _load_directory(gias_csv)
    lea = find_lea(lea_name)
    if lea is None:
        console.print(f"[red]Unknown LEA:[/red] {lea_name}")
        raise typer.Exit(2)
    schools: tuple[School, ...] = (
        directory.search(lea=lea, town=town) if town else directory.for_lea(lea)
    )
    table = Table(title=f"Schools in {lea.name}" + (f" / {town}" if town else ""))
    table.add_column("URN")
    table.add_column("Name", style="bold")
    table.add_column("Phase")
    table.add_column("Town")
    table.add_column("PD provider?")
    has_provider = set(SCHOOL_PD_PROVIDERS)
    for s in sorted(schools, key=lambda s: s.name):
        table.add_row(
            s.urn,
            s.name,
            s.phase.value,
            s.town or "",
            "[green]yes[/green]" if s.urn in has_provider else "-",
        )
    console.print(table)
    console.print(f"[dim]{len(schools)} schools.[/dim]")


@app.command("pd-days")
def pd_days(
    lea_name: str = typer.Argument(..., help="LEA name, e.g. 'Lincolnshire'"),
) -> None:
    """Aggregate published PD days from every school in an LEA that has a provider."""
    providers = pd_providers_for_lea(lea_name)
    if not providers:
        console.print(f"[yellow]No PD-day providers registered for {lea_name}.[/yellow]")
        raise typer.Exit(1)
    table = Table(title=f"PD days — schools in {lea_name}")
    table.add_column("School", style="bold")
    table.add_column("URN")
    table.add_column("Date")
    table.add_column("Year")
    table.add_column("Label")
    for cls in providers.values():
        try:
            provider = cls()
            days = provider.fetch()
        except Exception as exc:  # noqa: BLE001
            table.add_row(cls.school.name, cls.school.urn, "[red]error[/red]", "", str(exc))
            continue
        if not days:
            table.add_row(cls.school.name, cls.school.urn, "[dim]none found[/dim]", "", "")
            continue
        for d in days:
            table.add_row(
                cls.school.name,
                cls.school.urn,
                d.date.isoformat(),
                d.academic_year,
                d.label,
            )
    console.print(table)


if __name__ == "__main__":
    app()
