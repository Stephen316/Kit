<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Deterministic inference and affected archive rescans

A07 searches structurally aligned byte spans for values from separately recorded
measurements. One assessment covers one native stream layout and semantic
quantity. Search candidates declare primitive type, byte order, units, scale
and offset. Optional powers and control factors express bounded derived
relationships. Integer comparisons are exact. Floating-point comparisons use
encoded patterns, representable neighbors and a NumPy scan of remaining offsets
within the declared quantity tolerance.

The runner freezes candidate locations and identities before it reads challenge
and holdout results. Challenge controls can refute a candidate. The runner
requires distinct declared lineage labels for holdout. An audited design and
native ancestry record establishes independence for qualification.
The report retains each candidate
span, source and stream digest, conflicting observation and unresolved control
axis. A matching candidate remains partial evidence pending loader and
application proof.

## Run an assessment

Use Python 3.14 with the locked development dependency group. Register
`inference.fields` and `inference.rescan` with the supervisor. Use
`re/automation/InferenceRunner.py` followed by the whole-argument `{session}`
substitution as the runner. Generate its registry schema in the private state
directory.

```shell
uv run --frozen --group dev --python 3.14 python re/automation/InferenceRunner.py --schema
```

Bind the plan and each decoded stream through the [controller](../../../Reference/Research/ResearchController.md).
The plan contains `inference_version` set to 1, a `scope` label, a `quantity`
label, `encodings`, a nonnegative `tolerance`, `confounds` and
`observations`. Each observation identifies its `id`, independent
`lineage`, native archive `sha256`, `stream`, aligned byte `start` and
`length`, measured `value`, `controls`, bound input `role` and `split`.
The split is `discovery`, `challenge` or `holdout`. The plan's
`provenance.inputs` object is keyed by observation ID and contains the extracted
`archive_sha256`, `stream_sha256` and source evidence for each alignment.
The runner checks the archive identity and verifies the stream bytes against
the manifest pins.

Generate a controller schedule with `InferenceSchedule.py <request>`. Supply
`inference_version` set to 1, `scope`, `family`, `rule_version`,
`tool_version`, `plan_input`, `stream_inputs`, `archives`,
`distinguishing_evidence` and `depends_on`. The stream map binds each role
to a controller input. The archive map binds each native SHA-256 to a
`binding` and `format`. The supported rescan formats are `fusion.f3d`
and `solidworks.sldprt`. Submit the generated record with
`Controller.py --store <store> schedule <file>`.

To submit work ahead for multiple gaps, pass a `requests` array of these
records to the planner. Each request can include a `grids` array. Each grid
contains an A03 `job`, its `class` (`requested` or `standard`) and its
exclusive `installation` resource. The planner makes the assessment depend on
its requested grids. Requested grids take precedence at the next free
installation claim. The controller fills a target of ten queued grids per
installation from eligible supplied standard work, within store limits.
The scheduler rotates feature families within each lane and ranks jobs by open
dependents, distinct representative archives and distinguishing evidence.

Each rescan depends on its assessment's accepted controller result. An
unchanged fingerprint reuses the assessment and its counterexamples. Changed
rules and evidence invalidate only declared dependent jobs. Each rescan reads
one pinned native archive, records public reader output identity and retains
the unresolved inventory. A rescan does not apply a research hypothesis to the
production reader.

## Archive verification

The Workflow quality inference job runs `InferenceArchiveGate.py` through the real
controller and worker supervisor. It checks discovery and affected-file
rescans for the P03 pair. The negative direction control
distinguishes Fusion's signed scalar from SOLIDWORKS' positive magnitude and
separate direction flag. An unchanged resubmission must preserve all receipts.
A rule revision on one side must rerun only that assessment and its attached
archive jobs.

The P04 `inference.paired-gap` job takes a pinned paired report as its plan and
uses no stream input bindings. The termination report records the
blind-to-through-all change and measured volume difference. Its completed
counterexample releases rescans of the four affected archives. The one-body
capture leaves automatic and explicit selection compatible with the same
target. The controller parks this gap until distinguishing evidence arrives
and retains the two-body grid and affected archives in the receipt.

The hosted integration also exercises a synthetic disjoint-lineage holdout
and a repeated-lineage refusal. P03 and P04 remain discovery evidence. P05
remains reserved. Full milestone acceptance requires qualified A06 paired
evidence and fresh licensed Fusion readback.

The [hosted A07 job](https://github.com/TryUniCAD/Kit/actions/runs/43763760551/job/132964230460)
passed both the archive and scheduler verification at `ebe6130c`. It recorded
16 P03 rescans and four P04 termination rescans. An unchanged replay reused
all 18 P03 assessment and rescan receipts. A rule change reran nine jobs in one
scope. The P04 body-selection request parked with two dependent archives.
The synthetic holdout supported and contradicted the same frozen hypothesis
in separate runs, and the worker refused the repeated lineage.
[Hosted evidence artifact](https://github.com/TryUniCAD/Kit/actions/runs/43763760551/artifacts/14181740600)

The [standalone Fusion search](../Inference/FusionSignedDepthSearch.md) also
records the second signed-depth copy.

See [the paired history comparison](../Readers/Comparison/ArchivedCutHistory.md)
and [the automation step register](../../../Reference/Research/AutomationSteps.md).
