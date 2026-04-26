"""Interactive terminal UI for term-dates.

Launch with ``term-dates ui`` (or ``term-dates ui --gias-csv ...``).

Layout: three panes side by side.

  ┌───────────┬───────────┬─────────────────────────────┐
  │  LEAs     │  Schools  │  Calendar                   │
  │  filter   │  filter   │  (LEA events + PD days)     │
  └───────────┴───────────┴─────────────────────────────┘

Selecting an LEA refreshes the school list. Selecting a school fires an
async fetch in a Textual worker; the calendar pane shows progress until
the result lands. Press ``q`` to quit, ``/`` to jump to the focused
column's filter input, ``tab``/``shift+tab`` to move focus between panes.
"""

from __future__ import annotations

from datetime import date

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)

from term_dates.aggregate import build_school_calendar
from term_dates.lea import all_leas, custom_lea_names, implemented_lea_names
from term_dates.models import LEA, EventKind, School, SchoolCalendar
from term_dates.schools.gias import GIASSchoolDirectory
from term_dates.schools.registry import SCHOOL_PD_PROVIDERS

# A small palette mapping event kinds to row colours. Matches what most
# UK school calendars look like in print.
_KIND_STYLE: dict[str, str] = {
    EventKind.TERM_START.value: "bold green",
    EventKind.TERM_END.value: "green",
    EventKind.HALF_TERM_START.value: "bold yellow",
    EventKind.HALF_TERM_END.value: "yellow",
    EventKind.HOLIDAY_START.value: "bold cyan",
    EventKind.HOLIDAY_END.value: "cyan",
    EventKind.INSET.value: "bold magenta",
    EventKind.BANK_HOLIDAY.value: "red",
    "pd_day": "bold magenta",
}


class _LEAItem(ListItem):
    def __init__(self, lea: LEA, *, has_custom: bool, has_any: bool) -> None:
        if has_custom:
            marker = "[bold green]●[/]"
        elif has_any:
            marker = "[cyan]○[/]"
        else:
            marker = "[dim]·[/]"
        text = f"{marker} {lea.name}  [dim]· {lea.region}[/]"
        super().__init__(Label(text))
        self.lea = lea
        self.has_custom = has_custom
        self.has_any = has_any


class _SchoolItem(ListItem):
    def __init__(self, school: School, *, has_pd_provider: bool) -> None:
        marker = "[bold yellow]★[/]" if has_pd_provider else "[dim]·[/]"
        meta = (
            f"[dim]{school.town or '—'} · {school.phase.value} · URN {school.urn}[/]"
        )
        super().__init__(Label(f"{marker} {school.name}\n   {meta}"))
        self.school = school
        self.has_pd_provider = has_pd_provider


class TermDatesApp(App[None]):
    """Three-pane Textual app: LEAs → Schools → Calendar."""

    CSS = """
    Screen { layout: vertical; }
    #panes { height: 1fr; }
    #leas, #schools {
        width: 30%;
        border: round $panel;
        padding: 0 1;
        margin: 0;
    }
    #calendar {
        width: 1fr;
        border: round $panel;
        padding: 0 1;
        margin: 0;
    }
    Label.title { text-style: bold; padding: 0 1 1 1; color: $accent; }
    Input { margin: 0 0 1 0; }
    #calendar_status { padding: 0 1; height: auto; min-height: 2; }
    DataTable { height: 1fr; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("slash", "focus_search", "Filter focused column"),
        Binding("ctrl+r", "reload", "Reload calendar"),
    ]

    TITLE = "term-dates"
    SUB_TITLE = "English LEA term dates · per-school INSET / PD days"

    def __init__(self, *, directory: GIASSchoolDirectory) -> None:
        super().__init__()
        self._directory = directory
        self._all_leas: tuple[LEA, ...] = all_leas()
        self._impl_names: set[str] = set(implemented_lea_names())
        self._custom_names: set[str] = set(custom_lea_names())
        self._current_lea: LEA | None = None
        self._current_school: School | None = None

    # ---- layout ------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="panes"):
            with Vertical(id="leas"):
                yield Label("LEAs", classes="title")
                yield Input(placeholder="filter (e.g. 'lincoln')", id="lea_search")
                yield ListView(id="lea_list")
            with Vertical(id="schools"):
                yield Label("Schools", classes="title")
                yield Input(placeholder="filter by name or town", id="school_search")
                yield ListView(id="school_list")
            with Vertical(id="calendar"):
                yield Label("Calendar", classes="title")
                yield Static(
                    "[dim]Pick an LEA on the left.[/]",
                    id="calendar_status",
                )
                yield DataTable(id="calendar_table", zebra_stripes=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#calendar_table", DataTable)
        table.add_columns("Date", "Day", "Kind", "Year", "Label")
        table.cursor_type = "row"
        self._populate_leas("")
        self.query_one("#lea_search", Input).focus()

    # ---- population --------------------------------------------------

    def _populate_leas(self, query: str) -> None:
        list_view = self.query_one("#lea_list", ListView)
        list_view.clear()
        q = query.casefold().strip()
        # Curated first, then generic-with-URL, then unimplemented; alpha within.
        ordered = sorted(
            self._all_leas,
            key=lambda lea: (
                0 if lea.name in self._custom_names
                else (1 if lea.name in self._impl_names else 2),
                lea.name,
            ),
        )
        for lea in ordered:
            if q and q not in lea.name.casefold() and q not in lea.region.casefold():
                continue
            list_view.append(
                _LEAItem(
                    lea,
                    has_custom=lea.name in self._custom_names,
                    has_any=lea.name in self._impl_names,
                )
            )

    def _populate_schools(self, lea: LEA, query: str) -> None:
        list_view = self.query_one("#school_list", ListView)
        list_view.clear()
        schools = self._directory.for_lea(lea)
        if not schools:
            list_view.append(
                ListItem(
                    Label(
                        "[dim]No schools loaded for this LEA. "
                        "Pass --gias-csv for the full directory.[/]"
                    )
                )
            )
            return
        q = query.casefold().strip()
        filtered: list[School] = []
        for s in schools:
            if q:
                hay = f"{s.name} {s.town or ''}".casefold()
                if q not in hay:
                    continue
            filtered.append(s)
        # Schools with PD providers first, then alphabetical.
        filtered.sort(
            key=lambda s: (s.urn not in SCHOOL_PD_PROVIDERS, s.name)
        )
        # Cap shown rows to keep the UI snappy on full GIAS imports.
        for s in filtered[:500]:
            list_view.append(
                _SchoolItem(s, has_pd_provider=s.urn in SCHOOL_PD_PROVIDERS)
            )

    # ---- events ------------------------------------------------------

    @on(Input.Changed, "#lea_search")
    def _on_lea_search(self, event: Input.Changed) -> None:
        self._populate_leas(event.value)

    @on(Input.Changed, "#school_search")
    def _on_school_search(self, event: Input.Changed) -> None:
        if self._current_lea is not None:
            self._populate_schools(self._current_lea, event.value)

    @on(ListView.Selected, "#lea_list")
    def _on_lea_chosen(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, _LEAItem):
            self._current_lea = item.lea
            self._current_school = None
            self.query_one("#school_search", Input).value = ""
            self._populate_schools(item.lea, "")
            if item.has_custom:
                tag = "[green]curated provider[/]"
            elif item.has_any:
                tag = "[cyan]generic best-effort provider[/]"
            else:
                tag = "[yellow]no provider yet[/]"
            self.query_one("#calendar_status", Static).update(
                f"Selected [b]{item.lea.name}[/]  ·  {tag}.\n"
                "Pick a school to fetch its calendar."
            )

    @on(ListView.Selected, "#school_list")
    def _on_school_chosen(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, _SchoolItem):
            self._current_school = item.school
            self._fetch_calendar(item.school)

    def action_focus_search(self) -> None:
        """``/``: focus whichever search input belongs to the active column."""
        focused = self.focused
        if focused is None:
            self.query_one("#lea_search", Input).focus()
            return
        # Walk up to the containing pane (#leas / #schools / #calendar)
        node = focused
        while node is not None and getattr(node, "id", None) not in {
            "leas",
            "schools",
            "calendar",
        }:
            node = node.parent  # type: ignore[assignment]
        pane_id = getattr(node, "id", None) if node is not None else None
        if pane_id == "schools":
            self.query_one("#school_search", Input).focus()
        else:
            self.query_one("#lea_search", Input).focus()

    def action_reload(self) -> None:
        if self._current_school is not None:
            self._fetch_calendar(self._current_school)

    # ---- fetch + render ---------------------------------------------

    @work(thread=True, exclusive=True)
    def _fetch_calendar(self, school: School) -> None:
        self.call_from_thread(
            self.query_one("#calendar_status", Static).update,
            f"[bold]Fetching[/] {school.name} … [dim](this may take a few seconds)[/]",
        )
        self.call_from_thread(self.query_one("#calendar_table", DataTable).clear)
        try:
            cal = build_school_calendar(school)
        except Exception as exc:  # noqa: BLE001 — surface to the UI
            self.call_from_thread(
                self.query_one("#calendar_status", Static).update,
                f"[red]Error fetching {school.name}:[/] {exc}",
            )
            return
        self.call_from_thread(self._render_calendar, school, cal)

    def _render_calendar(self, school: School, cal: SchoolCalendar) -> None:
        status = self.query_one("#calendar_status", Static)
        table = self.query_one("#calendar_table", DataTable)
        table.clear()

        rows: list[tuple[date, str, str, str, str]] = []
        for ev in cal.lea_events:
            rows.append(
                (ev.date, ev.date.strftime("%a"), ev.kind.value, ev.academic_year, ev.label)
            )
        for pd in cal.pd_days:
            rows.append((pd.date, pd.date.strftime("%a"), "pd_day", pd.academic_year, pd.label))
        rows.sort()
        for d, weekday, kind, year, label in rows:
            style = _KIND_STYLE.get(kind, "")
            cells = (
                f"[{style}]{d.isoformat()}[/]" if style else d.isoformat(),
                weekday,
                f"[{style}]{kind}[/]" if style else kind,
                year,
                label,
            )
            table.add_row(*cells)

        sources_line = (
            "[dim]" + " · ".join(cal.sources) + "[/]"
            if cal.sources
            else "[dim]no sources reachable[/]"
        )
        status.update(
            f"[b]{school.name}[/]  ·  "
            f"[green]{len(cal.lea_events)}[/] LEA events  ·  "
            f"[magenta]{len(cal.pd_days)}[/] PD days\n"
            f"{sources_line}"
        )


def run(directory: GIASSchoolDirectory | None = None) -> None:
    """Launch the TUI. Falls back to the bundled providers if no directory."""
    if directory is None:
        schools = tuple(cls.school for cls in SCHOOL_PD_PROVIDERS.values())
        directory = GIASSchoolDirectory(schools=schools)
    TermDatesApp(directory=directory).run()
