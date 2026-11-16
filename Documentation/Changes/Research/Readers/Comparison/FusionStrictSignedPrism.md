<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Strict Fusion reverse blind prism reading

The strict Fusion reader accepts the measured P03 negative-distance save as a
metric XY, one-sided New Body extrusion. Its selected line loop still carries
the origin coincidence, four axis rules, and two sketch-owned dimensions.
The depth parameter keeps its own feature owner, signed value of −10 mm, and
literal `-( 10 mm )`. The neutral direction is +Z and the separate feature
taper is zero. The reader limits the wrapped literal to the verified negative
distance owner.

| Saved body check                  | Result                         |
| --------------------------------- | ------------------------------ |
| World bounds in mm                | `(0, 0, −10)..(40, 20, 0)`     |
| Centroid in mm                    | `(20, 10, −5)`                 |
| Volume in mm³                     | 8,000                          |
| Surface area in mm²               | 2,800                          |
| Shells / faces / edges / vertices | 1 / 6 / 12 / 8                 |
| Material                          | PrismMaterial-018, 7,850 kg/m³ |

Reading requires the same closed solid in the generic insertion journal and
saved snapshot. The journal starts at an empty state. Its live body key,
serializer, Design feature, operation map and body progenitor must agree.
The reader checks each native cap against its signed station and each side
against the original selected curve. It resolves both auxiliary sections to
separate snapshot roots at the XY profile, checks the reciprocal edge and coedge
attribute owners, and matches each section to the same four selected curves.
The native cache has the measured volume and centroid and the expected area
and origin-relative inertia for the signed solid.

The original P03 archive and capture limits are pinned by the
[paired direction replay](../FusionBossDirectionEvidence.md). Fusion 2706.1.17
provided the original same-process physical observations. The independent
SOLIDWORKS negative-direction control measured the same world extent, volume,
and centroid after a separate-process reopen.

The default partial read still retains the exact original native archive.
The strict result carries the complete V2 native state and its read-only marker.
The writer refuses the marked document and also refuses a marker-stripped V2
document after strict reprojection. Both V1 downgrade attempts emit zero bytes.
Prior metric, inch-display, and alternate-datum behavior is checked against the
established controls. The alternate YZ branch retains its original strict
refusal. Fresh-process Fusion reopening and edit qualification remain open for
this source.

The [generic topology replay](FusionSignedPrismEvidence.md) and
[V2 journal transport](FusionSignedPrismState.md) document the earlier
strict-refusal checkpoints. Their source proofs remain exact. The pinned process
reports now check the strict admission together with changed literal, depth,
taper, display-unit, body tag, and independent auxiliary section refusals.
The constrained and generic reports precede this reader at
`73c00ac7da8c3b1795d8380b0eb2970ed8f3698b`. The earlier journal replay is at
`6e1214ccafb760aaf50c2770152f1c4b4f9f8c77`.

| Process report          | Current SHA-256                                                    | Previous SHA-256                                                   |
| ----------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| Constrained prism       | `7c2bac73e8a3b6241ccddf0da5bbad20b8d4383fdfb9f43e7e091c438a82cef1` | `1a1330667b72bfdd5daee76f6def1f532e37f37e6d5a1ef4a9e24bb84fc1529d` |
| Generic signed geometry | `de418711fb9d347a4e03b883ef0538b5163df3a1653c48f896ab849a8251c807` | `d417c4fd244ddee97e7a3bdba40b1ddad9c4cc44809d9842b0f883f6b8f3e213` |
| Journal state           | `9cb493ca2f27ba479a0b8bd4dd13d88a54d643535e693e847a6e4259330c6f29` | `9f65aaa183fe35889b3a49587ff93bf962b9d0a6dd826610f163299e4fb91a45` |

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionConstrainedPrismEvidence.py
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionSignedPrism/VerifySignedPrism.py
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionSignedPrism/VerifyJournalState.py
```
