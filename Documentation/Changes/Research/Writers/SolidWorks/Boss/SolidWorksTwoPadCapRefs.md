<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS two-pad cap references

The A09 research constructor emits the selected top cap and four ordered boundary identities inside the upper sketch's face reference. It starts after the caller's `moFaceRef_c` header and ends at the guarded face return. This generation-19000 scope requires an earlier rectangular boss, its reached chooser cap, and the current archive allocation state.

The ordered occurrences come from the earlier chooser's typed allocations. Each new identity materializes its own feature reference and aliases the same earlier filed object. The constructor shares the existing chooser identity and return writers. The scope allocates ten compact objects and preserves the source feature, clock, cap selector, and boundary order.

The offline verifier rechecks the sealed SOLIDWORKS 34.4.1.1011 discovery receipt, four healthy stock controls, and 18 licensed observations. It reaches the earlier boss and its upper profile in each archive, corroborates the projected edge references, reads the selected occurrence and closes the enclosing face frame. The new 126-byte record matches every saved byte and the full post-record allocation state in all five independent saves.

A fresh generated chooser uses feature ID 74, clock `0x01020304`, and boundary order `32, 9, 18, 26`. Its cap occurrence reads back with allocation counter 36 to 46 and SHA-256 `94c7311cc84b5f06be3785d22cfd7abc380cf715b3eb5b4b9667a410ca2a9b92`. Twelve refusal controls cover a different earlier boss, a different filed object, mismatched feature and clock, a bottom cap, foreign or misordered boundaries, a duplicate occurrence, a forged allocation, a different generation, and corrupt or trailing data.

Run the verifier with the pinned Python environment and the retained private discovery directory.

```powershell
python -B re/solidworks/WriterResearch/TwoPadSupport/VerifyPadCap.py --run-directory $SealedTwoPadRun
```

The enclosing `moCompFace_c` remains an open construction dependency. Its local unit record begins with three words, 16384, 101, and 101, whose producers are unverified. The face header's classifier varies across the discovery grid. The rest of the upper profile, kernel ownership, and licensed load and edit evidence for a generated whole part are also open.
