<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Observe a live pilot inference on two-pad mass data

The models-off Windows pilot ran one assessment of the saved center of mass
Z coordinate in `Contents/CMgr`. Its input was the five
[licensed two-pad discovery saves](../Writers/SolidWorksTwoPadDiscovery.md).
Three independent values seeded discovery. A separately authored repeat
baseline and a changed base depth were reserved as same-family challenges.
P05 remains reserved for the frozen-rule holdout.

The controller appended six content-addressed inputs and one job in a single
transaction. The running supervisor at `1303a754` dispatched and settled the
only attempt. The controller recorded 2.49 seconds from submission to claim
and 5.32 seconds from claim to settlement. The process exited with code zero.
The fixed live report through event 198 records one claim and one completed
settlement. The earlier cutoff at event 187 remains replayable with the same
sealed digest. [Operating report](OfflinePilotEventReport.md)

The single candidate is a little-endian float64 in metres at offset 1250
within the five observed CMgr streams. Two discovery values and both challenge
values matched the encoded measurement exactly. The third discovery value
matched within the predeclared tolerance. The controller reports `partial`
confidence. Independent holdout evaluation and a generated document gain
remain open for this hypothesis.

The private admission manifest SHA-256 is
`8d28efb3cd280ca9dfefdf2b2fd855854fbfab527dfa97467b77aeef410ac6fb`.
The settled controller receipt SHA-256 is
`ab0a360f28177b1417a98cc458302c1d31d81ed144ead5366ed72f7ead4cbb1b`, and the
independent live-activity checkpoint SHA-256 is
`e0e82317ceea943abe6a83fa3d539c6f086125df1ab411b341b92542ae41cbb1`.

The store holds 24 completed jobs and three parked for evidence at this
cutoff. One completion occurred after the persistent supervisor started.
The two-week operating audit remains open.
