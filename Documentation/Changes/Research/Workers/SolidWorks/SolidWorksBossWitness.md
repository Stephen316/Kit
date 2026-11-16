<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Verify a generated SOLIDWORKS rectangular Boss witness

An independent fixture author supplies the generated SOLIDWORKS archive and its
exact generation report. A licensed application owner measures the candidate on
the pinned installation and retains both native phase receipts. Keep the archive
and receipts in a private directory and exchange their SHA-256 pins separately.

The verifier reads the plan and files. It requires no CAD installation and
does not launch the collector. A verified package or historical source readback
cannot provide the native phase receipts.

```sh
python re/automation/VerifySolidWorksBossWitness.py \
  --witness /private/BossWitness --plan-sha256 PLAN_SHA256
```

## Plan and retained inputs

Keep the immutable candidate as `Candidate.SLDPRT`, its owner's original generation
report as `Generation.json`, and the independently measured stock control as
`Control.SLDPRT`. Retain the exact package bytes whose digest the fresh fixture
reports as `archive_sha256`. Its standalone command prints JSON from an in-memory
package. The fixture owner supplies the corresponding private archive bytes.
The verifier checks the baseline against the report's `dimensions_mm`,
`bounds_metres`, `volume_m3` and `centroid_metres`. [Fresh fixture](../../Writers/SolidWorks/Metadata/SolidWorksFreshBossFixture.md)

In `Plan.json`, set `schema` to `1` and `scope` to
`generated-solidworks-rectangular-boss`. Record the following fields before the
licensed run.

| Field                                   | Value                                                                           |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| `source_revision`                       | Full source commit used to generate the fixture                                 |
| `build`, `image_sha256`                 | Exact licensed version and installed executable SHA-256                         |
| `candidate_sha256`, `generation_sha256` | SHA-256 of the original generated archive and retained report                   |
| `control`                               | Object containing stock `sha256`, `volume_m3` and three-coordinate `centroid_m` |
| `history`                               | Ordered native sketch and Boss names                                            |
| `drivers`                               | Ordered native width, height and depth dimension names                          |
| `shapes`                                | Objects keyed by `baseline`, `width`, `height` and `depth`                      |

Each shape uses four world-space `corners_m` in perimeter order, `depth_m` and
a unit world-space `direction` for the blind extrusion. The first edge measures
width and the next edge measures height. Order the corners in the authored
sketch winding so the sign in `dimensions_mm` agrees with the extrusion normal. Only the corresponding dimension
changes in each edited shape. Derive the four intended shapes from the fixture's
neutral geometry and edit targets. The verifier derives the expected volume and
centroid from that plan. It compares lengths within 0.1 nm and volumes within
10,000 μm³. Its direction checks allow dimensionless rounding.

## Native receipts

Use the shared oracle lease and an empty licensed desktop. The collection must
own its exact processes from launch through exit. Hash the archive that is
actually opened. Open a writable scratch copy in the first process. Measure the
baseline after rebuilding. Change only width, rebuild and measure, then restore
it, rebuild and remeasure. Repeat independently for height and depth. Save the
restored scratch archive, retain it privately as `Restored.SLDPRT`, and observe
the exact owned process exit normally. Launch a fresh owned process and reopen
that saved archive read-only. Measure it before and after rebuild. Each process
also opens and rebuilds the pinned stock control before and after the candidate.

Retain the observed results as `Edit.json` and `Reopen.json`. Both records use
`schema` 1, the plan `scope`, `status` `observed`, the matching `plan_sha256`
and `build`, and their exact `phase` values `edit` or `reopen`.

| Field                           | Required observation                                                                                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `owner`                         | `pid`, Windows creation FILETIME `created`, desktop `session`, `image_sha256`, `initial_documents` of zero and `verified` true from exact owned launch |
| `exit`                          | Same `pid` and `created`, observed exit FILETIME `finished`, `exit_code` zero and `drained` true                                                       |
| `input_sha256`, `output_sha256` | Candidate then restored archive for the edit. The same restored archive before and after reopen                                                        |
| `prior_sha256`                  | Null during edit; exact SHA-256 of `Edit.json` during reopen                                                                                           |
| `read_only`                     | False during edit and true during reopen                                                                                                               |
| `open`                          | Native `returned`, `errors` and `warnings`                                                                                                             |
| `save`                          | The same three native values for the restored edit-phase save. Null during reopen                                                                      |
| `controls`                      | `before` and `after` objects, each with stock `sha256`, `open`, `rebuild`, `body_count`, `volume_m3` and `centroid_m`                                  |
| `measurements`                  | Ordered native observations described below                                                                                                            |

The edit measurement stages are `baseline`, `width_edited`, `width_restored`,
`height_edited`, `height_restored`, `depth_edited` and `depth_restored`.
The reopen stages are `before_rebuild` and `after_rebuild`. Each record retains
its `stage`, ordered `history` and `boss_profile` name. Capture `blind`,
`fully_constrained`, `rebuilt`, `body_count`, `corners_m`, `direction`,
`depth_m`, `volume_m3` and `centroid_m` from the application. Use ordered
`drivers` with `axis`, `name`, observed feature `owner`, `driving` and `value_m`
for each dimension. The open and save records require a true return and zero
errors and warnings.

```sh
python re/automation/VerifySolidWorksBossWitness.py \
  --witness /private/BossWitness --plan-sha256 PLAN_SHA256 \
  --edit-sha256 EDIT_SHA256 --reopen-sha256 REOPEN_SHA256
```

The verified result covers that generated Boss, installation and measured
lifecycle. The previously retained
[rectangular omission witness](../../Writers/SolidWorks/SolidWorksArchiveOmissions.md)
contains a read-only depth edit and restore. The
[circular source witness](../../Readers/SolidWorks/SolidWorksDrivingEdits.md)
contains independent diameter and depth edits with a fresh reopen. Each provides
evidence within its own scope. The generated rectangular Boss and route-level
[A12 acceptance](../../../../Reference/Research/AutomationSteps.md#a12-solidworks-writer-research)
remain open until their own native evidence is available.

## Collect on the licensed Windows desktop

Run the companion from a clean checkout in the pinned Windows research Python
environment with pywin32. Compile against the registered interops before the
native run.

```powershell
python -B re/automation/RunSolidWorksBossWitness.py `
  --collector-revision COLLECTOR_COMMIT --compile-only
```

On the authorized empty licensed desktop, select a new owner-private output
directory outside the checkout. The input witness directory contains the pinned
plan, candidate, generation report and stock control.

```powershell
python -B re/automation/RunSolidWorksBossWitness.py `
  --collector-revision COLLECTOR_COMMIT `
  --witness C:\Private\BossPlan --plan-sha256 PLAN_SHA256 `
  --output C:\Private\BossObservation --timeout-seconds 300
```

The launcher holds the shared research oracle mutex across both phases. Each
phase uses a bounded STA collector and a separate direct SOLIDWORKS job. Their
processes are checked by held handles, desktop session and creation time. The
collector uses passive COM and confirms application job membership. It changes
only a private scratch copy. A normal application exit and natural job drain
are required before the saved bytes can enter fresh reopen.

The private output contains the original input pins, `Collector.json` with the
exact code revision and installed image and interop hashes, and per-phase
`Ready.json`, `Launch.json`, `Raw.json` and bounded logs. The wrapper checks
these records and seals `Edit.json` and `Reopen.json` for the standalone
verifier. It retains `Failure.json` when a phase cannot complete. Only the
independent verifier's successful result records completion of this native
witness.
