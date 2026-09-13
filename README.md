# satsumas

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

## Quickstart

```sh
uv sync            # or: pip install -e . && pip install pytest ruff pre-commit
pre-commit install
pytest
```
