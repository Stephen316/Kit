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
inference runner, with a two-session maximum and a reserve of two logical
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

The same store processed a scoped update when the format guard changed at `e6cf245e`. The four P04 termination rescans completed again with new receipts. The other 22 jobs retained their receipts and states, including the three waiting for evidence. The Windows supervisor admitted one active session at a time.

A15a still requires the two-week operating window and independent evidence for
recovery, readiness-to-acceptance timing, operator intervention and verified
document gains. This batch exercised only offline discovery. Its source and
seed schedule can be reconstructed with the [inference procedure](../Controller/DeterministicInference.md).

## Controlled supervisor interruption

The next private batch used source revision `0a70ff7eb2e9c5bd3744f1a4b27f25478b535488` and the locked CPython 3.14.6 environment. It scheduled P03 Fusion signed-depth discovery and the P04 two-body-selection evidence request. The launcher enabled one inference session, reserved two logical CPUs and 4 GiB of memory, and left native dispatch and models disabled. An initial preflight used the wrong schedule envelope and exited before launching the supervisor. The retained run used the multi-request schedule builder.

After observing the live P03 worker and its recorded process identity, the rehearsal driver terminated its own supervisor once and relaunched it with the same private store and configuration. The resumed supervisor recorded the prior attempt as an orphan. The old worker was no longer alive. The interrupted P03 assessment completed on attempt two. Nine jobs completed, three remained waiting for evidence, and none failed or remained queued. The report counts one deliberate intervention. The driver handled the restart without further operator action.

The 56.174-second activity window selected 79 controller events with SHA-256 `40b0183a93cd57c10a69c9cac59eab001cda8e41356c096ab64da758f2a196fe`. The activity report replayed byte-for-byte, SHA-256 `ddd487d3c137409037f9247b50488d02424a32c2ab81c18e00182bfaaf56193f`. The retained private run includes the controller store, both process logs, the interruption record and the run driver. The driver SHA-256 is `d7898c845612f3fc836517a657c30acd6a7a01e70653496e383f985860da0a88`.

This run checks recovery and bounded no-progress parking on real discovery jobs. The two-week operating witness, licensed dispatch and independently verified document gains remain open.
