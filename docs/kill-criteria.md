# Kill criteria

**Written:** 2026-09-13 (S0, before any other work)
**Review:** at the end of every stage, and on any trigger firing below.
**Status:** draft of record — the thresholds are deliberately numeric so that
they can be argued with. Argue with them now, not in month four.

This document exists so that the decision to stop, or to change shape, is made
once, in advance, by someone who is not yet emotionally invested in the outcome.
Every trigger below names an observable, a threshold, and a response. A trigger
with no observable is a mood, not a criterion.

---

## The structural risk

The entire RF data source is one satellite family — Meteor-M, LRPT at 137.9 MHz.
APT is gone: NOAA-19 was decommissioned 2025-08-13 and NOAA-15 on 2025-08-19,
and the last APT transmitter went off air with it (verified 2026-09-12;
re-verify in S1). There is no analog on-ramp and no second vendor. The
satellites are historically unreliable and geopolitically exposed.

The architecture responds to this by decoupling: S2–S4 (contract, ML,
pipeline, storage, observability) are built and tested against downloaded
surrogate granules and a replay harness, and require no RF at all. **If the sky
goes dark, the majority of the deliverable is already on disk.** That is the
mitigation. The criteria below define what happens when it is exercised.

---

## T1 — No LRPT downlink for 30 consecutive days

**Observable.** `satsumas` records, per predicted pass above the horizon mask,
whether a decode succeeded and — when it did not — the labelled cause
(scheduler miss, conflict skip, no signal, demod lock fail, FEC fail,
projection fail, storage fail). The trigger is: **zero successful decodes across
30 consecutive days in which at least one pass was predicted above the horizon
mask, with the ORBCOMM health probe green throughout.**

The ORBCOMM probe is what makes this criterion usable. ORBCOMM transmits
continuously in 137–138 MHz; an hourly job confirming its energy separates "our
receiver is deaf" from "the satellite did not transmit". Without it, 30 quiet
days is ambiguous and the criterion cannot fire. This is why the probe is in S5
and not in a backlog.

**Response.**

- *Probe green, no LRPT:* the sky is the problem, not the station. Do **not**
  buy hardware, rebuild the antenna, or rewrite the decoder. Stop RF
  development. The station keeps running, keeps predicting, and keeps reporting
  — an unattended station that correctly reports "nothing transmitted for 30
  days" is a working station and is written up as such. Work moves to S8 using
  the degraded-surrogate path (below) and to S9.
- *Probe red or flapping:* this is not T1. It is a station fault, and it is
  ordinary debugging work — antenna, feedline, SAW filter, LNA, SDR, USB power,
  host. The 30-day clock restarts when the probe is green again.
- *Probe green, LRPT present but never decoding:* also not T1. That is a demod
  or FEC problem with a labelled cause and a recorded IQ capture; it is S7 work.

**What is preserved.** Everything except S5–S7 outputs. The honest framing in
the write-up is: a complete ground station whose data source ceased to exist,
with the outage measured and reported by the station itself.

---

## T2 — The surrogate-to-real domain gap proves unbridgeable

**Observable.** At S8, the S3 model is run over self-received granules. The gap
is unbridgeable when, after **two** iterations on the degradation function (not
on the architecture — the improvement is almost always in the degradation
function), IoU on self-received granules remains **below the classical
thresholding baseline computed on those same granules**. Losing to the baseline
on real data is the bar; merely scoring lower than on surrogate data is
expected, and is a result rather than a failure.

The confound to rule out first: a projection or contract bug that makes
surrogate and real granules travel different code paths. This is why S2 puts
`geo/` in place before any ML, and why a surrogate granule and a self-received
granule are the same type. If they diverge, S8 measures a bug, not a domain gap.

**Response.** The measurement ships either way — a dated, reproducible
statement of how far AVHRR-trained segmentation transfers to real LRPT, with
the degradation function described in full, is a more interesting artefact than
a model that quietly works. What changes is only the framing of the headline:
from "learned segmentation running on self-received imagery" to "a measured
transfer failure, with the pipeline that measured it".

Concretely, in order of preference:

1. **Fine-tune on self-received granules** using weak labels from the same
   operational cloud-mask source used in S3, if enough clear-sky-varied passes
   have accumulated (target: 100+ granules across ≥2 seasons). Report both
   numbers — zero-shot transfer and fine-tuned — as the honest pair.
2. If not enough granules exist, **ship the classical baseline** as the
   production segmenter in the live pipeline, and ship the learned model as the
   surrogate-domain result it is. The station still segments; the write-up is
   about why the learned model did not survive the domain shift.
3. Do **not** respond by relabelling, by switching to a task the data supports
   better, or by quietly changing the metric. A changed task or metric after
   seeing the result is not a result.

---

## T3 — The minimum deliverable

If everything below is true, the time was justified regardless of what else
failed:

- **S2** — the granule contract exists, is documented, and a surrogate file
  round-trips through it. A surrogate granule and a self-received granule are
  the same type.
- **S3** — a segmentation model trained through an explicit degradation
  function, beating classical thresholding on a held-out set split *by pass
  date*, with metric (IoU) and split rationale stated.
- **S4** — the pipeline runs: replayed granules land in object storage with
  metadata in CloudNativePG, footprints queryable as PostGIS geometry, splits
  stored as rows, a Grafana panel showing pipeline health, and a synthetic
  failure paging via ntfy.
- **Docs** — `docs/ml.md` and `docs/postmortem.md`, dated and honest.

Note what is *not* in that list: any RF at all. S4's replay harness is what
makes this true, and is the reason it is not optional. **If the minimum
deliverable is not reachable without RF, the decoupling has failed and the plan
is wrong.**

Below that line the project is not worth continuing in its current shape, and
the response is to stop and write `docs/postmortem.md` rather than to reduce
scope again.

---

## T4 — Schedule and scope (the way this actually dies)

The named risks are not the likely cause of death; drift is. Two guards:

- **Scope.** S3 ships exactly one ML task: **Option A, cloud segmentation from
  weak labels**. Option B (Baltic sea-ice extent) is not kept alive as a
  stretch goal — that is precisely how the stage doubles. Reopening B requires
  editing this file first, with a date.
- **Time.** If any stage runs past **3× its planned effort**, stop and re-read
  this document before continuing. The overrun is the signal; what is being
  worked on when it overruns is usually not what the stage was for.
- **`notebooks/lib/` growth** is an early warning, not a style issue: a
  function used twice moves into `src/` with a test. If `lib/` is growing, the
  promotion rule has stopped being applied and the repo is drifting toward the
  notebook pile this project exists to not be.

---

## Decisions still open at S0

These are recorded so that they are decided deliberately at S1 rather than by
default:

1. **Hardware spend cap.** Antenna, SAW filter, LNA, SDR, feedline. The filter
   and LNA are mandatory, not contingency — Stockholm is a dense urban VHF
   environment and 137–138 MHz sits directly above the aviation band. Order
   during S1 regardless of stage order; lead time is the binding constraint.
   *Cap to be set at S1.*
2. **Rooftop / antenna-site access.** If access is not secured by the end of
   S5, T1's clock never starts and the RF track is blocked on something no
   amount of code will fix. *Decide at S1 whether this is a real constraint.*
3. **Elektro-L at 14.5°W.** Ten minutes of verification in S1, then close it.
   Almost certainly out (L-band dish). *Closed by default unless S1 says
   otherwise, in writing, here.*
