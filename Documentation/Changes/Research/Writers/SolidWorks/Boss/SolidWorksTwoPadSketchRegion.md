<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS two-pad sketch region

The A09 research constructor writes the active upper sketch's single region and guarded sketch return for generation 19000. It uses the caller's ordered local perimeter, the four line members and their active axis handles, and the current archive map. The lower sketch provides the inherited list, region, and line-handle classes. Seven new objects carry the region, its two lists, and the four local handles.

The native `sgSketch::Serialize` in SOLIDWORKS 34.4.1.1011 files its contour-list pointer at `sldmodu` RVA `0x1451e25`. The `moSketchRegion_c` writer files the boundary list at `0x816e4b`. The existing rectangle region transport supplies the typed handles and the empty silhouette, block, loop, and slot returns for this shape.

The verifier reaches the region through the sealed sketch's geometry, logical relation, four displays, and presentation environment. In all five licensed saves, the generated 88-byte region and return exactly match SHA-256 `c38ebd9dc0b53499b97c768e32a6304055874306375f4f0e2499a12a1a45cea4` and the full allocation state, from 365 to 372. The inline outline is `2, 1, 4, 3`. The following outer profile owns a separate projected chain `5, 6, 7, 8`. The five archives remain bound to 18 licensed observations and four healthy controls.

A fresh 23 mm contour follows a generated same-length relation, uses a different outline `31, 42, 22, 21`, and reads back with shifted allocations 16 to 23 and SHA-256 `f9752c14bd91f28f0d8682e2e291a09af7cbeddc86b68013671252075ae1d15f`. Nine refusal controls cover duplicate, foreign, and noncontinuous outlines, earlier and later sketch owners, an earlier line handle, a second region at the same station, and corrupt or trailing return bytes.

Run the verifier with the pinned Python environment and the retained private discovery directory.

```powershell
python -B re/solidworks/WriterResearch/TwoPadSketch/VerifyPadRegion.py --run-directory $SealedTwoPadRun
```

The four display records and presentation state 9 precede this region. Their construction, the following outer projected chain, and licensed acceptance of a complete generated two-pad part remain open.
