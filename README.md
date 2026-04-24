# term-dates

Aggregate **Local Education Authority (LEA) term dates** across England, with
optional **per-school PD-day polling** for individual schools selected from a
drop-down.

The package is built so that:

* Every English LEA the registry knows about (≈150) is browsable from a
  drop-down. Only LEAs with a registered provider can currently be *fetched* —
  contributing more is just a new `LEAProvider` subclass.
* Per-school PD/INSET days are scraped from each school's own website (LEAs
  publish term-skeletons, but PD days vary per school).
* The first worked example is **Lincolnshire**, with PD-day providers for
  three schools in the **City of Lincoln** (The Priory City of Lincoln Academy,
  Lincoln Christ's Hospital School, Lincoln Carlton Academy).

## Installation

```bash
pip install -e ".[dev]"
```

## CLI usage

```bash
# 1. Browse the registry (drop-down equivalents are non-interactive here):
term-dates list-leas
term-dates list-leas --implemented-only

# 2. Aggregate term dates across every LEA that has a provider:
term-dates aggregate
term-dates aggregate --lea Lincolnshire

# 3. Pick a school (drop-down) and print its full calendar:
term-dates school                              # interactive: LEA -> school
term-dates school --lea Lincolnshire           # pick school interactively
term-dates school --lea Lincolnshire --urn 137178   # fully scripted

# 4. List every school in an LEA (optionally narrowed by town):
term-dates schools-in-lea Lincolnshire --town Lincoln

# 5. Aggregate published PD/INSET days across every registered school in an LEA:
term-dates pd-days Lincolnshire
```

The school drop-down is sourced from a small bundled list by default. To get
**every English school** in the picker, pass the GIAS establishments CSV:

```bash
term-dates school --lea Lincolnshire --gias-csv ~/data/edubasealldata.csv
```

You can download `edubasealldata*.csv` from the
[GIAS *Downloads*](https://get-information-schools.service.gov.uk/Downloads)
page (the "All establishment data" extract).

## Library usage

```python
from term_dates.aggregate import build_school_calendar
from term_dates.schools.gias import GIASSchoolDirectory

directory = GIASSchoolDirectory.from_csv_path("edubasealldata.csv")
school = directory.search(lea="Lincolnshire", name_contains="Priory City")[0]
calendar = build_school_calendar(school)

print(school.name, "—", len(calendar.lea_events), "LEA events,",
      len(calendar.pd_days), "PD days")
for pd in calendar.pd_days:
    print(pd.date, pd.label)
```

## Architecture

```
term_dates/
├── models.py          # AcademicEvent, PDDay, School, LEA, …
├── http.py            # cached HTTP client with browser-like headers
├── parsing.py         # UK date parsers + PD-day vocabulary
├── lea/
│   ├── base.py        # LEAProvider ABC
│   ├── registry.py    # all 150 English LAs + provider lookup
│   ├── lincolnshire.py
│   └── _la_codes.py   # static LA reference (name + region + URL)
├── schools/
│   ├── base.py        # PDDayProvider ABC
│   ├── gias.py        # GIAS CSV loader & directory
│   ├── _extract.py    # generic PD-day extractor (HTML or text)
│   ├── registry.py    # URN -> provider class map
│   └── providers/
│       ├── priory_city_of_lincoln.py
│       ├── lincoln_christs_hospital.py
│       └── lincoln_carlton.py
├── aggregate.py       # high-level "aggregate everything" entry points
└── cli.py             # typer + questionary + rich CLI
```

## Adding a new LEA

```python
from term_dates.lea.base import LEAProvider
from term_dates.lea.registry import register_provider
from term_dates.models import LEA, TermDates


class KentProvider(LEAProvider):
    lea = LEA(code="886", name="Kent", region="South East",
              term_dates_url="https://www.kent.gov.uk/...")

    def fetch(self) -> TermDates:
        html = self.fetcher.get_text(self.lea.term_dates_url)
        return self.parse(html)

    def parse(self, html: str, *, source_url: str | None = None) -> TermDates:
        ...  # extract events with bs4 + term_dates.parsing helpers


register_provider("Kent", KentProvider)
```

## Adding a new school PD-day provider

```python
from term_dates.models import School, SchoolPhase
from term_dates.schools._extract import extract_pd_days, html_to_text
from term_dates.schools.base import PDDayProvider
from term_dates.schools.registry import register_pd_provider


class MySchoolProvider(PDDayProvider):
    school = School(urn="123456", name="My School", lea_code="...",
                    lea_name="...", phase=SchoolPhase.PRIMARY)
    source_url = "https://my-school.example/term-dates/"

    def fetch(self):
        return self.parse(self.fetcher.get_text(self.source_url))

    def parse(self, html):
        return extract_pd_days(html_to_text(html), default_year=2025)


register_pd_provider(MySchoolProvider.school.urn, MySchoolProvider)
```

## Tests

```bash
pytest
```

All tests are offline — they parse fixture HTML in `tests/fixtures/` rather
than hitting the live council/school sites (which sit behind WAFs that block
non-browser clients anyway). The City of Lincoln test
(`test_aggregate.py::test_aggregate_lincoln_pd_days_across_three_schools`)
combines the three Lincoln-school providers.

## Notes & caveats

* LEA term dates apply only to **community and voluntary-controlled** schools.
  Academies, free schools and voluntary-aided schools may publish their own
  dates — that is what the per-school PD-day providers are for.
* DfE 3-digit LA codes are **not** embedded in the static reference data
  because they change on local-government reorganisations. Look them up on
  GIAS when you need them.
* Many UK council and school sites are behind Cloudflare or similar WAFs. The
  bundled HTTP client sends a realistic browser User-Agent and retries with
  exponential back-off; you may still need to run from a residential IP for
  some sources.
* This project is unaffiliated with the Department for Education or any LEA.

## License

MIT — see `LICENSE`.
