<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Verify retained Fusion rectangle witness receipts

Use the manually prepared [rectangle witness directory](FusionOriginCoincidenceProbe.md#prepare-the-two-process-native-witness)
with its original plan, prepared input and proof, both native phase directories,
and the restored archive. Obtain each SHA-256 from the licensed witness owner
through an independently pinned handoff. Use the same procedure for the
[sketch-owned candidate](FusionOwnedDimensionProbe.md).

```sh
python re/Fusion/Reconstruction/DimensionAuthoring/VerifyWitness.py \
  --witness /private/FusionRectangleWitness \
  --plan-sha256 PLAN_SHA256 \
  --phase-a-receipt-sha256 PHASE_A_RECEIPT_SHA256 \
  --phase-b-receipt-sha256 PHASE_B_RECEIPT_SHA256 \
  --fusion-version 2706.1.17
```

Use a checkout containing the recorded generator and preparation revisions.
Its pinned witness helpers and healthy control must match the plan. The verifier
reads the existing directory layout. It never invokes a witness launcher or
changes the retained evidence.

It verifies both receipt and measurement hashes, the input and restored
archive bytes, the preparation and codec Git pins, and the recorded Fusion
build and two distinct process lifetimes. It checks both healthy controls in
each phase, the initial and reopened rectangles, and each independent driving
edit and restoration. It reports the observed profile areas and hashes without
requiring an installed CAD application.

The licensed Phase B harness checks that the first process exited before
accepting the restart. Offline verification checks the retained record of that
handoff using the owner-supplied hashes. These results cover the observed research
candidate. Public writer qualification, unattended dispatch and bidirectional
native acceptance have their own evidence gates.

The process fixture uses synthetic observations to exercise the retained
contract. It checks refusal of a mismatched receipt pin, reused process identity,
failed control and changed restored archive.

## Verified licensed replay

The licensed Fusion owner ran the verifier at `204ac0b8` against the two
original Fusion 2706.1.17 witness directories. Both returned
`verified_rectangle_witness`. The earlier sealed ZIP supplied the plan and
receipt pins. All 16 retained files matched that ZIP before and after replay.
The combined verification JSON SHA-256 is
`822ccd265b92510610148c9f67aa92c4835a9c4f3c64c783dfbad5df25a79d91`.
[Licensed replay report](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6922174876)
