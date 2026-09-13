# satsumas

<p align="center">
  <img src="docs/satsumas.png" alt="Mission patch: an orange with solar panels and a dish antenna, in orbit above the Earth, captioned SATSUMAS" width="320">
</p>

An unattended SDR ground station for polar-orbiting weather satellites, sited in
Stockholm (~59.33°N, 18.07°E). It predicts passes, captures 137 MHz baseband,
decodes the downlink to imagery, georeferences it onto a common grid, and runs
learned cloud segmentation over the result — with the learned component trained
first on downloaded surrogate imagery (AVHRR-class, ~1 km) and later fed by the
station's own receptions, so that the measured gap between the two is itself a
deliverable. It ships as code and a running service on an existing
Talos/Kubernetes + PostgreSQL + Prometheus stack, not as a notebook.

## Status

S0. The repository grows one region per stage; see [docs/plan.md](docs/plan.md)
for the stage list and [docs/kill-criteria.md](docs/kill-criteria.md) for what
stops it. Nothing is created before the stage that needs it — a directory
appears in the same commit as its first working contents.

## Toolchain

`uv` for environments, dependency resolution and locking; `ruff` for linting and
formatting; `pytest` for tests. No pip, no black, no isort, no flake8 —
`uv.lock` and `.python-version` are committed, so every environment and CI run
resolves identically.

## Quickstart

```sh
uv sync                       # creates .venv, installs the package + dev group
uv run pre-commit install
uv run pytest
uv run ruff check --fix .
uv run ruff format .
```

`uv` reads `.python-version` and fetches the interpreter itself; nothing needs
to be installed first. The package stays plain-`pip`-installable
(`pip install -e .`) because S0's done-criterion says so and because a capture
agent on a Pi should not need `uv` — but the development workflow is `uv run`.
