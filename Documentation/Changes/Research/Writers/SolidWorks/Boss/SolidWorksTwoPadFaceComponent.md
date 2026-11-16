<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS two-pad face component prefix

The A09 research constructor emits the 104-byte matched-owner prefix of the upper sketch's local `moCompFace_c` reference. It begins with the compact component definition and returns after its absent alias byte, immediately before the separate face header. It requires the earlier configured atom bound to the lower cap's chooser, the same local part alias, and explicit matched-owner evidence tied to those exact allocations.

In SOLIDWORKS 34.4.1.1011, the component-face constructor obtains the selected body's `gcBody_w::getAtomId` at `sldmodu` RVA `0x6a5578` and stores it in two reference fields. The enclosing `moCompRef_c` writes its flags at `0xa66340` and those atom fields at `0xa66382` and `0xa6638e`. The selected-face resolver sets bit `0x4000` at `0x6cffba` after matching the face's owning atom among multiple body candidates. Its alternate branch sets that bit at `0x6d05e6` after comparing the selected face's body with the expected candidate. These words follow the local unit child and belong to the enclosing component reference.

All five sealed saves preserve the same local part, the lower atom 101, and the earlier chooser cap. The upper transfer binds independently to atom 102. Fresh emission matches the entire prefix and the complete post-prefix allocation state in all five saves, with SHA-256 `e861c412ffe25a0bd9e1add3bdcb69ccf448c610bb98e2b6c269179c838fe6df`. The verifier also corroborates the next face header against the continuous typed archive walk and rechecks 18 licensed observations and four stock controls.

A fresh offline case generates and reads two distinct configured atoms and an earlier chooser. It selects atom 271 and allocates a shifted component prefix with SHA-256 `a343bdfc336892e1acc3df75a2deb5ee00938c8a6d14a4fb445ed558a13c75d8`. Twelve refusal controls cover absent and contradictory match evidence, another typed part, transfer, or cap, invalid prior allocations, an incompatible existing class, and malformed or trailing bytes.

Run the verifier with the pinned Python environment and the retained private discovery directory.

```powershell
python -B re/solidworks/WriterResearch/TwoPadSupport/VerifyPadComp.py --run-directory $SealedTwoPadRun
```

The face header still needs the selected earlier kernel face handle. The installed resolver caches the selected face at RVA `0x6cff81`, and the face serializer files the low 32 bits of that cache at `0xa62ae8`. The sealed saves preserve the matched-owner branch and its ownership joins. They contain no live candidate inventory or generated kernel-face selection evidence. The complete face shell and a licensed load, rebuild, and edit of a generated whole part remain open.
