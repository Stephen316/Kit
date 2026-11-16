<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Strict Fusion source reading for the constrained XY first boss

The packaged strict reader admits a metric, positive XY, first one-sided
blind boss with an origin-coincident, fully constrained rectangle. The proof
checks the exact ordered point operands, four line-axis rules, the distinct
fixed origin, two separately owned sketch parameters, and the closed perimeter
selected by the extrusion. It checks the reciprocal native parameter,
feature, update, and compute graph. Blind depth and the explicit zero taper
retain separate ownership. The existing body history and topology, material
asset and mass-property, placement, scope, and snapshot checks still apply.

Strict output carries the complete typed native state and a read-only marker.
The existing partial reader retains the original archive bytes. The Fusion
writer refuses the new strict output even if the caller removes the marker.
This evidence records Fusion source reading. Target authoring, fresh native
target edit and reopen, cross-CAD conversion qualification, and A05c completion
remain separate.

The inch-display discovery archive retains the active unit system's exact
typed ModelingLength choice and reciprocal owner. The strict document exposes
`source_display_units` as `"in"` alongside geometry and length values in
millimeters. The original literal drivers still read `40 mm`, `20 mm`,
`10 mm`, and `0.0 deg`. The strict document also retains the complete native
V2 state and the saved material, body history, and snapshot. The public Fusion
and SOLIDWORKS write requests refuse the source and emit zero bytes.

## Reproduce the pinned discovery report

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionConstrainedPrismEvidence.py
```

The report reads the original P03 discovery commit
`89c25945f5833ad9c3a1c6c683df510b5702dd54`. Fusion 2706.1.17 licensed
readback used the same process for the baseline and three independent parameter
edits. The repeat export uses a measurement taken before that export.
The inch variant's reopened document reports inch display independently.
SOLIDWORKS 34.4.1 supplies the separately reopened paired physical evidence.
The independently recorded centroids and volumes agree with the checked body.
The report retains the qualification blockers from both capture receipts.

| Archive                            | Width, height, depth in mm | Volume in mm³ |
| ---------------------------------- | -------------------------- | ------------- |
| Baseline, repeat, and inch display | 40, 20, 10                 | 8000          |
| Width edit                         | 41, 20, 10                 | 8200          |
| Height edit                        | 40, 23, 10                 | 9200          |
| Depth edit                         | 40, 20, 12                 | 9600          |

The YZ and negative-direction discovery archives remain refused.
Eight wire-readable in-memory mutations exercise a broken endpoint, duplicate
axis assignment, third distinct dimension, translated placement, reference
driver, unexpected rule, reciprocal nonzero taper, and an added unapproved
Design entity. Two additional wire-readable mutations refuse an unsupported
display length and a ModelingLength choice owned by another unit system.
Eight earlier strict rectangle, prism, circular, cylindrical, and frustum
controls retain their original neutral fingerprints. The normalized report
SHA-256 is `1a1330667b72bfdd5daee76f6def1f532e37f37e6d5a1ef4a9e24bb84fc1529d`.

The original metric-only checkpoint `f688178cbceed27a521be78787898db285573eb9`
recorded the inch refusal and report SHA-256
`b3324c35a37b1065e4d6fa325056a57afbf2f9f7f2a1067e8b64fbc607bb6bb6`.
