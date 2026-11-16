<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Typed saved Fusion P04 Cut openings

The replay reads only the original sealed P04 blind baseline A, blind repeat
B, and through-all control in Fusion and SOLIDWORKS. It verifies the native
archives and original application observations at
`89c25945f5833ad9c3a1c6c683df510b5702dd54`. The scope follows the
[paired archive comparison](ArchivedCutHistory.md) and the
[saved body actor evidence](../FusionCutJournalEvidence.md).

The generic Fusion decoder transports each complete typed document through
V2 JSON and reconstructs its native journal and snapshot parts byte for byte
in memory. The journal materializes an empty initial state, the earlier
rectangular Boss, and a distinct closed Cut result. The two retained
`TimeAttrib` owners match the original Boss and Cut actor clocks. The prior
body and current body share the historical handle reported by the partial
reader. The target, support cap, and the through-all extent reference join
back to Design body 309 and Boss feature 277.

The openings are native inner rings with reversed winding relative to their
own outer rings. In these captures, the inner ring comes first. Typed
coedges, edges, vertices, and the containing face establish each ring's role.
The proof compares the inner footprint with the selected Cut sketch and
integrates signed tetrahedra over all rings to derive volume and centroid.

| Case          | Opening heights in mm | Floor height in mm | Faces / edges / vertices | Volume in mm³ | Centroid in mm    |
| ------------- | --------------------- | ------------------ | ------------------------ | ------------- | ----------------- |
| Blind A and B | 10                    | 6                  | 11 / 24 / 16             | 7,680         | `(20, 10, 4.875)` |
| Through-all   | 0 and 10              | Absent             | 10 / 24 / 16             | 7,200         | `(20, 10, 5)`     |

The three observed outer bounds are `(0, 0, 0)..(40, 20, 10)` mm. The
geometric measures agree with the original observations and both public
partial readers. The typed snapshots contain tool-sized geometry at slot 1.
Additional closed roots match the earlier Boss dimensions. The through-all
snapshot contains two Boss-sized roots. Their persisted role identities
remain open.

The public strict route reaches Design object 338 and reports
`Unknown native Fusion entity class`. Eight distinct GUIDs across these cases
fall outside the strict catalogue. Changing the saved opening winding or
current body actor clock survives generic typed decoding and fails the
geometric or ownership proof. Applying the wrong termination or an unrelated
claimed target also fails. The ordinary planar result reader reports that a
face requires one owned outer loop. The public Fusion writer emits zero bytes for the partial
source and for the same neutral source carrying the verified V2 state.

Fusion 2706.1.17 provided same-process observations for baseline A and
through-all, and an observation before the baseline B repeat export.
SOLIDWORKS 34.4.1 used its original separate-process reopen. Fresh Fusion
reopen diagnostics, live supporting-face, relation and dimension targets,
and editable acceptance remain open for these exact sources.

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionCutState/VerifyCutState.py
```

The LF-normalized JSON report has SHA-256
`98fee890f42e66362571036c7b627c3d2b9ee478bbcaad5a9776125ca68c9668`. The hosted archive gate pins this replay.
