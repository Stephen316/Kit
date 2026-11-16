<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Report an authenticated archive gate failure

The [paired archive observer](HostedPairedArchiveGate.md) can report `archive_gate_failed` for one exact failed gate step in an authenticated terminal Actions job. The selected predecessors must have passed and the selected successors must have been skipped. The observer checks the repository, pull request, run attempt, Actions check, and workflow blob against the audited merge candidate. It rechecks current head, base and run identity before returning the failure.

The failure report names the gate step and its ordered outcomes. An audited merge candidate records the source available for review. Verifying what the job tested still requires the hosted archive receipt. A cancelled job or an upstream failure with no selected gate failure keeps its previous refusal. A superseding run reports `superseded`.

The [batch release](PairedCiBatchRelease.md) reports the failure with `waiting_ci`. The observer does not request a success artifact, and the release opens no ledger transaction for this outcome. Member attribution and durable release still require their own evidence.

The hosted Linux job at PR head `e6cf245e` recorded a failed archive test at step 14, followed by skipped receipt and upload steps 15 and 16. The `050e58f5` run had the same sequence before superseding cancellation; it supplies step evidence without eligible terminal authority. The upgraded hosted transcript fixture uses that observed order and checks success, refusal and supersession boundaries. Hosted execution of the new cases remains pending. [Terminal failure](https://github.com/TryUniCAD/Kit/actions/runs/43886271791/job/133365360324) · [Superseded job](https://github.com/TryUniCAD/Kit/actions/runs/43898514513/job/133408682839)
