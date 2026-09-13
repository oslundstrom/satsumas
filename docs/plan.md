# Project brief

**Revision date:** 2026-09-12. Reproduced here verbatim as the plan the
repository grows against. Claims about the sky rot fastest — re-verify in S1 and
record the result in `docs/survey.md`, not here.

---

**SDR weather-satellite ground station with cloud segmentation**

**Site:** Stockholm, Sweden (~59.33°N, 18.07°E)

## Objective

Build an unattended ground station that receives polar-orbiting weather
satellites, decodes the downlink to imagery, georeferences it, and runs learned
segmentation on the result. Deliver as code + running service, not a notebook.

The learned component is trained first, on downloaded surrogate data, and is
later fed by the station's own receptions. The measured gap between the two is
itself a deliverable.

## Context

- Operator already runs: RTL-SDR hardware, Raspberry Pi fleet
  (Ansible-provisioned), single-node Talos/Kubernetes cluster managed as GitOps,
  PostgreSQL, Longhorn storage, Prometheus/Grafana/Alertmanager, ntfy.
- Prefer integrating with that stack over standalone scripts.
- Single node. No HA anywhere. Design for recoverability, not availability.

## Status of the sky (verified 2026-09-12 — re-verify before acting)

APT is dead. NOAA-19 was decommissioned 2025-08-13, NOAA-15 on 2025-08-19, and
the last APT transmitter went off air with it. There is no analog on-ramp.

Remaining 137 MHz targets, to be confirmed in S1:

| Satellite | Mode | Freq | Notes |
|---|---|---|---|
| Meteor-M N2-4 | LRPT | 137.9 MHz (137.1 backup) | Primary target |
| Meteor-M N2-3 | LRPT | 137.9 MHz | Antenna partially undeployed, reduced signal |
| Meteor-M N2-2 | — | — | LRPT terminated 2019, HRPT only |

Both active Meteors share 137.9 MHz. One SDR means overlapping passes are a
scheduling conflict, not a parallel capture.

**This is the project's largest risk.** The entire RF data source is one Russian
satellite family, historically unreliable and geopolitically exposed. The
architecture below decouples the ML and infrastructure work from it
deliberately.

## Out of scope

- Geostationary reception. (Possible exception: Elektro-L at 14.5°W may be
  marginally visible at low elevation. L-band dish, so still almost certainly
  out. Ten minutes of verification in S1, then close it.)
- EUMETCast (DVB-S2 + tuner card, not SDR).
- Sentinel-2 / EuroSAT reception (X-band to dedicated ground stations — download
  the data instead if that dataset is wanted).
- Transmitting anything.

## Resolution reality

MSU-MR is ~1 km/px at nadir. Land-use classification is not possible at this
scale. Choose ML tasks visible at 1–4 km.

---

# How the repository grows

One repository, `satsumas`. It starts as a few files and accretes exactly one
new region per stage. Nothing is created before the stage that needs it — no
empty packages, no placeholder Dockerfiles, no `deploy/` directory full of
commented YAML.

The rule: **a directory appears in the same commit as its first working
contents.** If you can't fill it, you don't need it yet.

Two conventions established at S0 and never broken afterwards:

- **`satsumas.<module>` is importable from anywhere, including notebooks.**
  Notebooks import; they do not define.
- **Every stage leaves behind a test and a doc.** Not comprehensive coverage —
  one test that would have caught the bug you actually hit, and one page of
  what you learned.

Layering rules are added to an import-linter config as the modules appear, so
the constraints grow with the code rather than being retrofitted.

---

# Stages

Ordering principle: do the work that cannot be blocked first. RF can stall on
hardware lead times, weather, rooftop access, or a satellite going dark. ML and
infrastructure cannot.

S4 and S5 are independent and run in parallel. **Order the RF hardware during S1
regardless of stage order** — lead time is the binding constraint, and "we'll
add RF later" is where projects die.

---

## S0 — Repository and kill criteria

The whole repo, at the end of this stage:

```
satsumas/
├── pyproject.toml          # package `satsumas`, no extras yet
├── README.md               # one paragraph: what this is
├── src/satsumas/__init__.py
├── tests/
└── docs/kill-criteria.md
```

Write down, before anything else, what causes this project to stop or change
shape.

- If no LRPT satellite transmits for 30 consecutive days, what happens?
- If the surrogate-to-real domain gap proves unbridgeable, what ships instead?
- What is the minimum deliverable that still justifies the time spent?

**Done when:** `pip install -e .` works and `docs/kill-criteria.md` is dated.

---

## S1 — Survey

**Adds:** `src/satsumas/catalog/`, `notebooks/explore/`, `docs/survey.md`

`catalog/` is the survey output *as data*, not prose — YAML plus a loader.
Active satellites, frequencies, modes, TLE source config, horizon mask polygon.
Read at runtime, so a satellite going dark is a config change rather than a code
change.

`notebooks/explore/` appears here because S1 is the first stage with something
to look at. Disposable, dated files: `2026-09-14-pass-elevation-distribution.ipynb`.
`nbstripout` pre-commit hook goes in with the directory.

**(a) Confirm the sky.** Active satellites, frequencies, modes. Target list with
expected passes/day and elevation distribution for Stockholm. Do a
compass-and-inclinometer horizon survey and encode the result as a polygon, so
"expected passes" means passes actually visible from the antenna site.

**(b) Choose the surrogate.** Which downloadable sensor most resembles what the
station will eventually produce. Almost certainly AVHRR/3 on MetOp — MSU-MR was
designed as an AVHRR analogue, with comparable bands and ~1 km resolution, free
from the EUMETSAT Data Store. Confirm which MetOp platforms are still flying and
whether MetOp-SG changes the picture.

VIIRS and SLSTR are easier to obtain and worse for transfer: different bands,
different resolutions, radiometry far better than anything you will receive.

**(c) Gate — do this before S3 starts.** Obtain one real LRPT product you did
not capture: a SatDump sample recording, a SatNOGS observation, someone's
published IQ. Half a day, and it tells you concretely what channels, artifacts
and geometry you are targeting. Nothing in S3 begins until this is on disk.

**Done when:** `docs/survey.md` (every claim dated), a 7-day predicted pass
table, horizon mask in `catalog/`, a named surrogate dataset, and one real LRPT
product on disk.

---

## S2 — The granule contract

**Adds:** `src/satsumas/db/`, `src/satsumas/geo/`

Define the typed object everything downstream consumes: channel set, grid,
projection, quality statistics, provenance. A surrogate granule and a
self-received granule are the same type.

`geo/` arrives now, not later, because the contract is meaningless without the
projection that produces it — and because the surrogate and the real data must
travel the same code path or the S8 domain gap measures your own bug.

`db/` at this stage is schema and migrations only. No running database yet.

This is the hinge the whole reorder turns on. If it's wrong you find out in S8,
which is the most expensive place to find out. Spend longer on it than the stage
length suggests.

**Done when:** the type exists, is documented in the README, and a surrogate
file round-trips through it.

---

## S3 — ML on surrogate data

**Adds:** `src/satsumas/data/`, `src/satsumas/model/`, `src/satsumas/eval/`,
`notebooks/reports/`, `notebooks/lib/`, `datasets/`, `docs/ml.md`, `[ml]` extra

`datasets/` holds manifests and splits. Not pixels, ever.

`notebooks/reports/` starts with one notebook, `training_run`, and grows to
three by S8. Jupytext pairing from the first commit — the `.py` is source of
truth, the `.ipynb` is generated. Reviewable diffs, no committed PNGs of the
Baltic.

`notebooks/lib/` is the waiting room for helpers too ugly for `src/`. Promotion
test: a function used twice moves into `src/` with a test. If `lib/` is growing,
something is wrong.

### Task — pick one

*Option A, cloud segmentation.* Do not hand-label. Derive weak labels from an
existing operational cloud mask (NWC SAF, CM SAF, or a co-located VIIRS/SLSTR
cloud product) reprojected onto your granules. You trade annotation effort for
registration error, which is more tractable and more interesting to write up.

*Option B, Baltic / Gulf of Bothnia sea-ice extent.* Seasonal, visible at 1 km,
with SMHI/FMI ice charts as reference labels. It contains Option A as a
prerequisite: at 59°N in midwinter the visible channels are nearly useless, so
you work in thermal IR, where the dominant confounder is cloud. If you choose B,
cloud screening is an explicit component and evaluation is restricted to
clear-sky pixels.

**Recommendation:** A as the deliverable. Do not keep B alive as a "stretch" —
that is how this stage quietly doubles in scope.

### Degradation function

Build this early and train through it. This is the real research contribution;
everything else in the stage is standard.

Real LRPT is not clean AVHRR L1B: a subset of channels, 8-bit, dropped lines,
corrupted packets, truncated passes. Subsample to the LRPT channel set, quantise,
drop random line runs, add noise, reproject through `satsumas.geo`. The model
then learns on something close to its eventual input, and S8 becomes
verification rather than surprise.

### Evaluation

Baseline: classical thresholding. Report against it.

Metric: IoU, not accuracy — cloud fraction is wildly imbalanced. Split by *pass
date*, not by patch; adjacent patches from one granule are near-identical and
random splits leak badly. State the metric and the split.

**Done when:** the model beats the classical baseline on a held-out set, with
metric and split stated, and `training_run` executes non-interactively and
writes its metrics through `satsumas.eval`.

---

## S4 — Pipeline, storage, observability

**Adds:** `deploy/`, `images/base/`, `images/inference/`, the replay harness,
`docs/metrics.md`

Built against a replay feed of surrogate granules. No RF required.

`deploy/` is the GitOps target and the only directory the reconciler watches, so
a notebook commit cannot trigger a reconcile. It appears with real manifests:
`cnpg/`, `monitoring/`, `dashboards/`.

`images/base/` and `images/inference/` share a base so training and inference
environments cannot drift apart.

**Replay harness.** A command that feeds historical granules through the live
pipeline at accelerated speed. How you test this stage before any RF exists, how
you validate changes later, how you reprocess everything when the decoder
improves. Do not skip it.

**Database.** CloudNativePG with the PostGIS image. `instances: 1` — one node,
so this buys declarative config, automated backups with PITR, and the built-in
Prometheus exporter, not HA. PITR is the real prize for an unattended system.

- CNPG guidance prefers local directly-attached volumes over replicated network
  storage, since CNPG replicates at the Postgres layer. Longhorn underneath CNPG
  on a single node adds latency and a failure mode and buys nothing. Use a
  local-path provisioner, back up to object storage, WAL on a separate volume.
- **Check the backup API before writing manifests** — barman-cloud support moved
  from in-tree config to a plugin in recent CNPG versions, so older tutorials
  will steer you wrong.
- Imagery to object storage. Pointers only in Postgres.
- Granule footprints as PostGIS geometry. "Every granule intersecting the Gulf
  of Bothnia with >60% clear-sky pixels in February" becomes one statement.
- **Store dataset splits as rows, not files.** "Which granules were in the
  held-out set for run 47" is a question you will ask in six months.
- Notebooks connect through a read-only role, enforced by which secret the pod
  mounts, not by discipline.

**Metrics and alerting.** Instrument failure *cause* as a label: scheduler miss,
pass skipped by conflict, no signal, demod lock fail, FEC fail, projection fail,
storage fail. A skipped pass is not a failed pass. These labels are the
difference between a station that alerts and a station that explains.

Do not alert on consecutive failures — that pages you through satellite outages.
Alert on *no successful decode in 24h given at least one predicted pass above
the horizon mask*.

`docs/metrics.md` names every metric and its meaning. In six months you will not
remember whether `passes_attempted` included conflict-skipped passes.

**Done when:** replayed granules land in object storage with metadata in CNPG, a
Grafana panel shows pipeline health, and a synthetic failure pages via ntfy.

---

## S5 — RF front end

**Adds:** `src/satsumas/capture/`, `ansible/`, `[capture]` extra, `docs/rf.md`

The `[capture]` extra pulls SDR bindings and nothing else — no torch on a
Raspberry Pi. This is the point where the optional-extras split earns itself.

`ansible/` starts with one role: provision a Pi as a capture agent.

137 MHz antenna. V-dipole is sufficient, QFH better.

**SAW filter + LNA are mandatory, not contingency.** Stockholm is a dense urban
VHF environment and 137–138 MHz sits directly above the aviation band, sharing
spectrum with ORBCOMM. Budget for them up front.

**ORBCOMM as a permanent health beacon.** You have lost APT as a "does the chain
work at all" test signal. ORBCOMM transmits continuously in 137–138 MHz and is
trivially detectable. An hourly job confirming ORBCOMM energy separates "our
receiver is deaf" from "the satellite didn't transmit" — exactly the
self-reporting property that differentiates this project.

**Done when:** a raw IQ capture of one pass shows the expected signal, and the
ORBCOMM probe reports green in Grafana.

---

## S6 — Prediction and capture

**Adds:** `src/satsumas/predict/`, `images/capture-agent/`,
`images/scheduler/`, `deploy/cronjobs/`

TLEs from Celestrak, refreshed on a schedule, staleness handled explicitly and
surfaced as a metric. Predict passes, apply the horizon mask from `catalog/`,
resolve conflicts between the two Meteors by max elevation — and *record the
choice*, distinctly from a failure.

**Doppler:** do not retune hardware per-sample. Record baseband wide enough
(~150 kHz) and let SatDump's costas loop track the ±3 kHz. One less moving part.

**Split capture from processing.** The Pi is a dumb capture agent that writes
baseband to object storage. A Kubernetes Job triggered on new objects does
decode and projection. Fits the GitOps stack better than running SatDump live on
the Pi, and makes reprocessing trivial when the decoder improves.

**Storage discipline:** raw IQ at 2.4 MSPS is ~7 GB/pass; decimated baseband
~450 MB. Keep baseband only for *failed* decodes, 14-day retention, discard on
success.

**Done when:** the station wakes, captures, and sleeps unattended for 48h.

---

## S7 — Decode and georeference

**Adds:** `src/satsumas/decode/`, `images/decoder/`, `granule_qc` report
notebook

SatDump is the expected tool — wrap, do not reimplement. Parse its output,
extract quality statistics, emit a granule conforming to the S2 contract.

`granule_qc` runs per decode: image, quality stats, footprint. The artifact you
look at when a pass seems wrong.

Project using the same `satsumas.geo` code path as the surrogate data.

**Done when:** a recognisable, correctly-georeferenced image is produced
end-to-end from RF, automatically, and overlays on a coastline reference.

---

## S8 — Close the loop

**Adds:** `domain_gap` report notebook, CI execution of `notebooks/reports/`

Run self-received granules through the model trained in S3. Measure the gap.
Report it honestly: if the degradation function was well-chosen the gap is
small; if not, that finding is also a result.

Iterate on the degradation function, not on the architecture — that is almost
always where the improvement lives.

CI now executes `notebooks/reports/` on every PR touching `satsumas.data` or
`satsumas.model`. A broken loader fails the build rather than surfacing three
weeks later.

**Done when:** `domain_gap` executes in CI and its numbers are in `docs/ml.md`.

---

## S9 — Write-up

**Adds:** `docs/postmortem.md`, bootstrap script, final README

- README: architecture, granule contract, quickstart.
- `docs/rf.md`: antenna build, link budget, horizon mask, measured SNR vs
  elevation.
- `docs/ml.md`: baseline, model, metric, split rationale, domain gap. The
  degradation function deserves its own section — it is the part nobody else has
  done.
- `docs/postmortem.md`: what failed and why. The section that makes the project
  credible to a reader.
- One-command bootstrap: fresh Pi + fresh cluster to running station, documented
  and tested once. Cuttable if time is tight — you will rebuild by hand once and
  survive.
- One paragraph suitable for a CV bullet.

---

# The repository at the end

Shown for orientation only. Do not create this up front.

```
satsumas/
├── pyproject.toml              # extras: [capture] [ml] [notebook]
├── .importlinter               # layering rules, grown per stage
├── src/satsumas/
│   ├── catalog/                # S1 — survey output as data
│   ├── db/                     # S2 — schema, granule contract
│   ├── geo/                    # S2 — projection to the common grid
│   ├── data/                   # S3 — loading, degradation, splits
│   ├── model/                  # S3 — baseline + U-Net
│   ├── eval/                   # S3 — metrics, eval entrypoint
│   ├── capture/                # S5 — SDR, baseband, ORBCOMM probe
│   ├── predict/                # S6 — TLE, passes, conflicts
│   └── decode/                 # S7 — SatDump wrapper, quality stats
├── notebooks/
│   ├── explore/                # S1 — disposable, dated
│   ├── reports/                # S3 — executed by CI
│   └── lib/                    # S3 — waiting room, keep small
├── images/                     # S4, S6, S7
├── deploy/                     # S4 — GitOps target
├── ansible/                    # S5
├── datasets/                   # S3 — manifests + splits, not pixels
├── docs/
└── tests/
```

**Layering rules** (added as modules appear): `capture` and `decode` may not
import `model`; nothing in `src/` may import from `notebooks/`; `catalog` imports
nothing else in the package.

**Notebook hygiene:** run Jupyter locally, port-forwarded to CNPG, reading
granules over the network. In-cluster Jupyter only once granules are large
enough that pulling them hurts — a long-lived notebook pod competes with decode
jobs for memory, which is an annoying way to lose a pass.

# Notes

- Prefer boring, observable infrastructure over clever RF. The differentiator is
  that it runs unattended and reports its own health.
- `docs/survey.md` rots fastest. Date every claim in it.
