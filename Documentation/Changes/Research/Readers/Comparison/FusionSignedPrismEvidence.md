<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Generic signed P03 prism replay

The replay reads the original positive XY baseline, width edit, height edit,
depth edit, and negative-depth archive at P03 discovery revision
`89c25945f5833ad9c3a1c6c683df510b5702dd54`. It uses the existing generic journal
and snapshot decoders and reproduces all ten original B-rep parts byte for byte
in memory. Fusion 2706.1.17 supplied the independent same-process source
measurements. The report retains the source receipt's qualification limits.
[Signed extent evidence](../FusionBossDirectionEvidence.md)

Generic journal materialization verifies the empty initial state and the
current insertion. The planar reader resolves the single untransformed solid
to six quadrilateral faces, twelve shared edges, and eight vertices. The
snapshot independently supplies the same solid and two distinct rectangular
sections on the original sketch plane. Both auxiliary roots contain 33
distinct region records. The replay checks their typed edge and coedge owners
and matches their physical endpoints to the selected Design curves.

The negative archive's state advances from 2 to 4 with 101 insertions. Its
generic body key 0 maps to Design body 309 and extrusion 277. Operation 301
owns the six body faces and the body tag's secondary ID 7 agrees with the
saved body progenitor. Cap 1 stays at the sketch plane. Cap 2 follows the
signed endpoint. The negative archive joins side label 4 to curve 107 and
label 6 to curve 103. The positive controls have the opposite two pairings.
Each pairing comes from its saved Design side recipe and the matched face
footprint.

| P03 case       | Signed depth in mm | Volume in mm³ | Centroid in mm |
| -------------- | -----------------: | ------------: | -------------- |
| Baseline       |                 10 |         8,000 | 20, 10, 5      |
| Width edit     |                 10 |         8,200 | 20.5, 10, 5    |
| Height edit    |                 10 |         9,200 | 20, 11.5, 5    |
| Depth edit     |                 12 |         9,600 | 20, 10, 6      |
| Negative depth |                −10 |         8,000 | 20, 10, −5     |

Changing only the negative history body tag's secondary ID to 8 leaves the
wire and closed geometry readable. The reciprocal Design join refuses it.
The four positive public strict reads still return the body. The negative
archive retains its public strict refusal and the alternate YZ path remains
outside this evidence. No native output is saved. [Scoped strict reader](FusionStrictConstrainedPrism.md)

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/automation/FusionSignedPrism/VerifySignedPrism.py
```

Two independent Python 3.14 runs produced normalized report SHA-256
`d417c4fd244ddee97e7a3bdba40b1ddad9c4cc44809d9842b0f883f6b8f3e213`.
