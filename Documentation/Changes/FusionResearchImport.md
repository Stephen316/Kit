<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Fusion research import and explicit reader

The Fusion study and saved evidence are imported under `re/Fusion/Study`, with
feature notes and reproduction guidance under `re/Fusion/Notes`. Historical
research files retain their original bytes and provenance. The research exemption
applies only beneath `re/`; it does not establish production acceptance.

The complete PR also adds Fusion parsing and projection modules, shared feature
models, and FreeCAD native feature writing and edit reconciliation under `src/`,
with corresponding integration coverage. These SDK changes are part of the PR;
the change is larger than a standalone corpus import.

Production adapter discovery excludes `Fusion`, and public registry discovery
must not advertise or resolve `fusion.f3d` or its `f3d` alias. Research callers
explicitly instantiate `FusionReader` with `ReadOptions`, as described in the
[research reader guide](../../re/Fusion/Notes/SdkReader.md). Tests opt in through
`tests/convert/FusionRead.py`; this is not a production registration mechanism.

The explicit reader projects qualified history, parameter, sketch, body, and
assembly data. Unsupported history selection, feature coverage, and archive
compression variants have documented limits in the reader and feature notes.
FreeCAD writing and readback cover selected feature families; this PR does not
establish full parametric translation, complete native Fusion writing, or
target-application acceptance for arbitrary input.

Verification for the compliance repair consists of Black, Prettier, and diff
whitespace checks. Remote CI must verify the complete changed revision. The two
reported steering failures are corrected by extracting catalog alias assertions
and shortening the rationale-policy integration test name, preserving the
assertions. No tests were executed locally during this repair. Earlier study
audit results are historical evidence, not newly executed acceptance checks.
Heavy acceptance remains deferred to the merge-group candidate, and review
approval remains a separate current-head requirement.

See the [Fusion feature index](../../re/Fusion/README.md),
[saved-file workflow](../../re/Fusion/Notes/Workflow.md), and
[merge queue operations](../../MergeQueue.md).
