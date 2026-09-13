# Learning goals

**Written:** 2026-09-13 (S0)

This project is a vehicle for learning three things: **SQL/databases**, **ML**,
and **SDR**. That is the actual deliverable; the ground station is the excuse.
The consequence is a rule that overrides convenience everywhere else in this
repo:

> **If something is on the learning list, you write it. If it is not, automate
> it, copy it, or have an assistant write it — and say so in the stage doc.**

The distinction matters because the failure mode of an AI-assisted project is a
working repository the author cannot explain. A ground station that runs but
whose PostGIS query you could not reconstruct at a whiteboard has not taught you
SQL; it has taught you to prompt.

## What is yours to write

- Every SQL statement, schema, index and migration in `src/satsumas/db/`.
- Every model, loss, training loop and metric in `src/satsumas/model/` and
  `src/satsumas/eval/`, and the whole degradation function in
  `src/satsumas/data/`.
- Every DSP decision in `src/satsumas/capture/` and `src/satsumas/predict/`:
  sample rate, decimation, bandwidth, gain, the Doppler argument.

## What is not

Packaging, CI, Kubernetes manifests, Ansible roles, Dockerfiles, retries, glue.
Boring infrastructure is a means here, not an end — you already run this stack.
Use help freely and move on.

The boundary case is `src/satsumas/decode/`: SatDump is wrapped, not
reimplemented, so the *decoder* is not yours to write — but understanding what
its quality statistics mean (Viterbi BER, deframer lock, packet loss) is, and
S7's doc is where you demonstrate that.

---

## Per-stage mapping

| Stage | SQL / DB | ML | SDR |
|---|---|---|---|
| S1 Survey | — | — | Link geometry, horizon mask, what LRPT actually is |
| S2 Contract | Schema design, migrations, PostGIS types | — | Projection geometry |
| S3 ML | Splits as data, not files | **The bulk of it** | Degradation function = SDR knowledge encoded as code |
| S4 Pipeline | **The bulk of it** — CNPG, PITR, spatial queries, roles | Inference in a service | — |
| S5 RF front end | — | — | **The bulk of it** — antenna, filter, LNA, noise floor |
| S6 Capture | Scheduling state, conflict records | — | Doppler, sample rate, storage budget |
| S7 Decode | Quality stats as columns | — | Demod → FEC → frames → imagery |
| S8 Loop | Query the gap | Domain shift, honest evaluation | Why real data differs |

Note where the columns overlap: **S3's degradation function is the single place
where SDR understanding and ML understanding have to be the same
understanding.** It is described in the brief as the real research contribution,
and it is also the stage where the three subjects stop being three subjects. If
one topic is going to get shortchanged, make sure it is not that one.

---

## Checkpoints — "can you do this unaided?"

Ask at the end of each stage. A "no" is not a reason to redo the stage; it is a
reason to write the stage doc more carefully, or to write one small thing again
from scratch with the reference closed.

- **S2.** Write the granule table's DDL from memory, including the PostGIS
  geometry column, its SRID, and the index you would need for a footprint
  intersection query. Explain why that index type.
- **S3.** Explain why IoU rather than accuracy, and why the split is by pass
  date rather than by patch, to someone who suggests random patch splits. Then
  explain what your degradation function does and which real LRPT artefact each
  step imitates.
- **S4.** Write, unaided, the query for "every granule intersecting the Gulf of
  Bothnia with >60% clear-sky pixels in February". Then explain what PITR would
  actually restore, and what it would not.
- **S5.** Explain what the SAW filter and LNA each do, in that order, and why
  the order matters. Sketch the noise figure argument.
- **S6.** Justify the recorded baseband bandwidth from the Doppler shift and the
  signal bandwidth, on paper.
- **S7.** Read a SatDump quality report and say which stage of the chain failed
  and why.
- **S8.** State the domain gap number and defend it against "your test set
  leaked".

---

## How to use an assistant without hollowing this out

- **Ask for the concept before the code.** "Explain how a Costas loop tracks
  Doppler" beats "write the capture script".
- **Write it first, then have it reviewed.** A review of your wrong SQL teaches
  more than correct SQL handed over.
- **Never paste code into `db/`, `model/`, `eval/`, `data/`, `capture/` or
  `predict/` that you cannot explain line by line.** If you cannot, that is the
  next thing to read, not the next thing to commit.
- **Each stage doc says what you learned, in your own words.** That is the
  point of "every stage leaves behind a test and a doc", and it is the artefact
  that proves the learning happened.

## Suggested background reading

Chosen so that each stage has one thing to read *before* starting it, rather
than a reading list to finish first.

- **SQL/DB** — the PostgreSQL manual on indexes and EXPLAIN; PostGIS
  introduction (spatial types, SRIDs, GiST); the CloudNativePG docs on backup
  and recovery. Read the CNPG backup docs at S4, not now: the backup API moved
  from in-tree config to a plugin recently and older tutorials are wrong.
- **ML** — anything on segmentation metrics and class imbalance; U-Net's
  original paper; and, more usefully than either, a paper on domain shift in
  remote sensing.
- **SDR** — a receiver noise-figure/link-budget primer; the LRPT signal
  description (QPSK, Viterbi, Reed–Solomon, 72 kSym/s); SatDump's own docs on
  what its pipeline stages do.
