<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS two-pad sketch display owners

The A09 research constructor writes one inherited `moSkDimHandleValG2_c` record for an upper sketch dimension. The 115-byte record reuses the existing empty component and reference framing, aliases the active `sgSketch`, and files its signed local ordinal. It allocates one handle object and returns before annotation placement.

The native sketch handle reads its sketch alias at `sldmodu` RVA `0x16f50b3` and its dimension ordinal at `0x16f50e7` in SOLIDWORKS 34.4.1.1011. The constructor checks the current sketch and display allocation station, the ordered local dimensions and their typed point handles, and the distinct horizontal, vertical, and origin-relative operands before writing. The caller supplies the requested native dimension identity.

The licensed authoring source selects the width edge, height edge, left origin offset, and bottom origin offset in that order. The authored and independently reopened feature snapshots corroborate the same order and values. Width, left, and bottom are driving. The height is driven and retains its own display. In all five saved archives the local ordinals are `0, 1, 2, 3`, visual indices are `12, 13, 14, 15`, and native dimension identities are `36, 37, 39, 40`. The 20 generated owner records match all bytes and the full allocation states. The sealed evidence includes 18 licensed observations and four healthy stock controls.

A fresh 23 mm sketch with another sketch earlier in the map owns the four distinct dimensions `81, 84, 88, 101`. All four links read back at shifted allocations. Eight refusal controls cover an earlier or later sketch owner, mismatched slots, swapped equal-length roles and operand order, and tampered serialized sketch and ordinal fields.

Run the verifier with the pinned Python environment and the retained private discovery directory.

```powershell
python -B re/solidworks/WriterResearch/TwoPadSketch/VerifyPadDimLink.py --run-directory $SealedTwoPadRun
```

The display opening, placement, cache, and tail remain separate construction work. The neighboring presentation state 9 belongs to the signed `sgSketch` member at offset `0x130`, initialized to 1 at `0x1353e6c` and filed at `0x14517e2`. Its state-9 producer and licensed acceptance of a complete generated upper sketch remain open.
