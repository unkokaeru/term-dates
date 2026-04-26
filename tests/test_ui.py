"""Smoke tests for the Textual TUI in term_dates.ui.

These exercise the UI without touching the network: they construct the app
with the bundled provider-registered schools, drive a few key presses
through ``run_test``'s pilot, and assert that filtering and selection
populate the dependent panes.
"""

from __future__ import annotations

import pytest

from term_dates.schools.gias import GIASSchoolDirectory
from term_dates.schools.registry import SCHOOL_PD_PROVIDERS
from term_dates.ui import TermDatesApp, _LEAItem, _SchoolItem


@pytest.fixture
def directory() -> GIASSchoolDirectory:
    schools = tuple(cls.school for cls in SCHOOL_PD_PROVIDERS.values())
    return GIASSchoolDirectory(schools=schools)


async def test_initial_render_has_three_panes(directory: GIASSchoolDirectory) -> None:
    app = TermDatesApp(directory=directory)
    async with app.run_test(size=(140, 40)) as pilot:
        await pilot.pause()
        # Each pane has its title label.
        assert app.query_one("#leas") is not None
        assert app.query_one("#schools") is not None
        assert app.query_one("#calendar") is not None


async def test_lea_filter_narrows_list(directory: GIASSchoolDirectory) -> None:
    app = TermDatesApp(directory=directory)
    async with app.run_test(size=(140, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import ListView

        lv = app.query_one("#lea_list", ListView)
        all_count = len(lv.children)
        assert all_count > 100  # 152-ish English LAs in the registry

        # Filter to lincolnshire.
        await pilot.click("#lea_search")
        for ch in "lincolnshire":
            await pilot.press(ch)
        await pilot.pause()

        filtered = lv.children
        assert 0 < len(filtered) < all_count
        assert any(
            isinstance(c, _LEAItem) and c.lea.name == "Lincolnshire" for c in filtered
        )


async def test_lea_selection_populates_schools(
    directory: GIASSchoolDirectory,
) -> None:
    app = TermDatesApp(directory=directory)
    async with app.run_test(size=(140, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import ListView

        # Filter, focus list, pick first item.
        await pilot.click("#lea_search")
        for ch in "lincolnshire":
            await pilot.press(ch)
        await pilot.pause()

        lea_list = app.query_one("#lea_list", ListView)
        lea_list.focus()
        lea_list.index = 0
        await pilot.press("enter")
        await pilot.pause()

        school_list = app.query_one("#school_list", ListView)
        names = {
            c.school.name
            for c in school_list.children
            if isinstance(c, _SchoolItem)
        }
        assert "Lincoln Carlton Academy" in names
        assert "Lincoln Christ's Hospital School" in names
        assert "The Priory City of Lincoln Academy" in names
