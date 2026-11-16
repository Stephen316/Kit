<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Licensed Fusion P03 baseline witness

Prepare the plan on the signed-in macOS Fusion host from a checkout containing the witness and candidate sources. Use the private baseline archive and generation manifest supplied by the authoring owner. Preparation rechecks the original SOLIDWORKS receipt and baseline archive, then reopens the exact prepared Fusion archive offline and compares its full saved profile, binding, dependency and body evidence with the manifest. [Candidate evidence](FusionSourceBossProbe.md)

For the recorded private bundle, the manifest SHA-256 is `f7074e12dafd45c329cf4ef11cae6443a7471ed948499b317134b7b5736bbb31`. The baseline archive has 99,883 bytes and SHA-256 `4e77340e23e5b3f6354990a08c39f329d1549a3bcddb2aaf893037c3ab88ce64`. The plan retains the original generation revision and independently matches the generator files in the operator's checkout. For a later regeneration, use the new input hashes certified by its owner.

```sh
PYTHONPATH=src:re/automation uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/Fusion/Reconstruction/DimensionAuthoring/SourceBossWitness.py prepare \
  --candidate /private/P03Candidates --output /private/P03BossWitness \
  --manifest-sha256 f7074e12dafd45c329cf4ef11cae6443a7471ed948499b317134b7b5736bbb31 \
  --archive-sha256 4e77340e23e5b3f6354990a08c39f329d1549a3bcddb2aaf893037c3ab88ce64 \
  --fusion-version 2706.1.17
```

Start Fusion after preparation with no documents open. In Text Commands, run `Python.RunScript "/private/P03BossWitness/phase-a.py"`. The phase opens the unchanged 30,000 mm³ control before and after the candidate. It verifies the distinct Origin coincidence, fully constrained XY sketch and size drivers, and the exact four live sketch entities selected by the Boss. It measures the one-sided blind New Body, depth and zero taper ownership, caps, body count, topology, bounds, volume and center of mass before and after rebuild. [Fusion profile selection API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExtrudeFeature_profile.htm), [Fusion profile curve identity API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ProfileCurve_sketchEntity.htm)

Phase A edits `width_mm` to 41 mm, `height_mm` to 23 mm and `depth_mm` to 12 mm independently. Each edit must rebuild to 8,200, 9,200 or 9,600 mm³ respectively and retain the other expressions. A successful restore after each edit returns to the original 40 × 20 × 10 mm and 8,000 mm³ before exporting the restored archive.

After `phase-a/receipt.json` records `complete`, quit Fusion normally and confirm that its process exited. Start the same build without open documents. Run `Python.RunScript "/private/P03BossWitness/phase-b.py"`. Phase B checks the prior process exit and imports the exact SHA-pinned restored archive. It rechecks the original expressions, live profile and body before and after rebuild between the same healthy controls.

Retain the plan, both receipts and measurements, prepared inputs and restored archive privately. Supply the plan and both receipt hashes from the licensed operator's handoff. The verifier reopens only the saved evidence and never launches Fusion.

```sh
PYTHONPATH=src:re/automation uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/Fusion/Reconstruction/DimensionAuthoring/SourceBossWitness.py verify \
  --witness /private/P03BossWitness --plan-sha256 "$PLAN_SHA256" \
  --phase-a-receipt-sha256 "$PHASE_A_RECEIPT_SHA256" \
  --phase-b-receipt-sha256 "$PHASE_B_RECEIPT_SHA256"
```

Use `inspect-plan` with `--witness` and `--plan-sha256` to check custody before native execution. The prepared plan and offline readback leave native acceptance pending. Physical material and mass parity remain outside this witness.
