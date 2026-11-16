<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS two-pad projected profile chain

The A09 research constructor writes the 88-byte inherited `moSketchChain_c` record after the active upper sketch's region return. It takes the actual upper profile and sketch, a typed earlier cap chooser, and four caller-owned projected edge identities in cap order. The projected IDs remain separate from the upper sketch's local perimeter. The inherited compact class adds one chain object.

The generation-19000 writer uses the established rectangle chain fields. In SOLIDWORKS 34.4.1.1011, the chain serializer at `sldmodu` RVA `0x11363b0` files the two counted arrays, the fixed state fields, and the optional child returns. This scope uses the ordinary empty handles, pair map, and trim children, with the count and presence fields owned by the enclosing profile.

The verifier reads the earlier chooser, the upper inline sketch, and the separate projected edge records. The filed edge-order list and ordered cap references join projected IDs `5, 6, 7, 8` to boundary occurrences `4, 1, 2, 3`. All five sealed saves match the exact new 88-byte chain and full allocation state from 372 to 373, with SHA-256 `582c038ec855304a686bbf3d39b326ed7fe83f3b14ff1d9502db7dbb18e09cd9`. The following kernel packet remains separately bounded at 1206 or 1210 bytes. The continued support reader reaches the same earlier cap, and the custody check corroborates 18 licensed observations and four healthy stock controls.

A fresh generated chooser and inline region supply different cap sides `32, 9, 18, 26` and projected IDs `44, 61, 82, 105`. The chain uses shifted allocations 48 to 49 and reads back with SHA-256 `5d60940ba3025e09a2ef0f3e9540019b5b98db1d48e878963654fc56cfc13bef`. Nine refusals cover duplicate, overlapping or oversized projected IDs, swapped sides, foreign file and clock, a second chain at the same station, and corrupted or trailing return bytes.

Run the verifier with the pinned Python environment and the retained private discovery directory.

```powershell
python -B re/solidworks/WriterResearch/TwoPadSupport/VerifyPadChain.py --run-directory $SealedTwoPadRun
```

The embedded cap geometry, its independent link to the projected IDs, and the selected kernel face handle still need construction evidence. Licensed load, rebuild, and edit evidence remains required for a complete generated two-pad part.
