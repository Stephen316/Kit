<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# In-memory Fusion P03 to SOLIDWORKS Boss research candidates

The replay admits the four SHA-pinned positive XY Fusion archives from the
original P03 discovery revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`.
The source proof checks the actual selected four-line loop, shared endpoint
identities, distinct origin coincidence, exact ordered width and height
operands, and the direct positive blind depth owner. Fusion 2706.1.17
reopened the originals in the source capture process. The independently
recorded source volumes and centroids agree with the strict reader. [Strict Fusion source evidence](FusionStrictConstrainedPrism.md)

The research constructor supplies those measured inputs to the existing
SOLIDWORKS ordinary Boss package builders. The caller authors the fresh
save identity, classification fields, appearance labels, archive timestamps
and database UUIDs. Independent archive readback resolves the Front Plane and
Origin, the selected outline, two sketch drivers, one blind Boss depth, the
body atom, the header bounds, and the CMgr mass and centroid. The Fusion source
physical density of 7,850 kg/m³ is bound separately to the SOLIDWORKS Definition
tail and Config-0 material field. The compatibility content label and unset
compatibility density are read back separately. [Ordinary package context](../../Writers/SolidWorks/Metadata/SolidWorksFreshBossFixture.md)

| Original P03 case | Volume in mm³ | Centroid in mm | Saved mass in kg |
| ----------------- | ------------: | -------------- | ---------------: |
| Baseline          |         8,000 | 20, 10, 5      |          0.06280 |
| Width edit        |         8,200 | 20.5, 10, 5    |          0.06437 |
| Height edit       |         9,200 | 20, 11.5, 5    |          0.07222 |
| Depth edit        |         9,600 | 20, 10, 6      |          0.07536 |

The target emits three owned driving dimension records. Its straight end preserves
the zero-taper geometry. Fusion's independently owned `d4` remains in the
report with its owner, ID, literal and value. The report also accounts for the
source literal syntax, body name, configuration descriptors, named material,
native BREP, graphics and caches. The target body uses the generated sketch
and feature representation and typed saved body metadata. The physical and
ghost partitions, lightweight cache and display-list members are absent.
Both original Fusion read paths still reach the same public portability and
SOLIDWORKS writer refusals. Native SOLIDWORKS open, edit, restore, rebuild and
fresh reopen of generated output remain unobserved. [Reverse path write refusals](FusionToSolidWorksBossInput.md)

## Reproduce the offline report

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/solidworks/WriterResearch/VerifyInverseP03Boss.py --synthetic-context
```

The replay uses explicitly synthetic archive contexts for the four source
variants and emits JSON. The packages exist only in its process memory. The
synthetic context SHA-256 is
`53b844fbefbc922f5e161c132e9d3850ab87febc2f96663cc39261d01832b66b`.
Two independent Python 3.14 processes produced normalized report SHA-256
`d28bb9f8028fa2820faccd2427ed9c46c4e206b43bf22f7eb9ab00e5c23bf9e6`.

A caller can pass `--contexts FILE --contexts-sha256 SHA256` with one ordinary
save context for each of `baseline-a`, `edit-width_mm-41`,
`edit-height_mm-23` and `edit-depth_mm-12`. Pass `-` for standard input. The
Definition terminal density must agree with the checked source density.
Caller-supplied classification fields describe archive inputs. Licensed
execution and public target admission qualify separately.
