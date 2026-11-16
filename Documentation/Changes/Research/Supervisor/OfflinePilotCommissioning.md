<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Commission the models-off offline pilot

On 16 November 2026, the Windows supervisor processed the first private offline
pilot batch at source revision `ce538c42b9ae0535d40e70ec64ac7a097411ee3e`, based on
`1d294381340a36ce8e4d9e288e73d995da12fcd7`. The commissioned environment used
CPython 3.14.6 and the frozen project lock. The registry enabled only the
inference runner, with two available session slots and a reserve of two logical
CPUs and 4 GiB of memory. Model providers and application dispatch were disabled.
The inputs came from the P03 signed-depth and P04 termination and body-selection
discovery grids. P05 remained reserved.

The controller retained 26 jobs. Twenty-three completed, comprising two signed
depth assessments, one paired termination assessment and 20 archive rescans.
The one-body result could not distinguish automatic from explicit body
selection. Its assessment settled in `waiting_evidence`, and both dependent
rescans stayed parked with zero attempts. There were 24 claims and no orphan
or stale settlements. The supervisor drained the runnable queue without
operator action after submission.

The frozen controller window began at Unix time `1794839102.8747602` and ended
at `1794839313.0`. It selected events 1–166 with SHA-256
`820276b1f826ae1858b4f8673c169258957bc858d1f9a87cc2c28fe65f817ef2`. The
[activity report](OfflinePilotEventReport.md) replayed byte-for-byte for that
window. Its SHA-256 is
`54a03aa267193c76ec3d8c9af4904e24cb84161b955613822883f959a0fc7faa`.
The longest observed chain was one assessment plus one rescan, totaling
10.10 seconds of controller attempt time.

A15a still requires the two-week operating window and independent evidence for
recovery, readiness-to-acceptance timing, operator intervention and verified
document gains. This batch exercised only offline discovery. Its source and
seed schedule can be reconstructed with the [inference procedure](../Controller/DeterministicInference.md).
