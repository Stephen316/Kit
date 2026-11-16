<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# SOLIDWORKS two-pad configuration mass subrecord

This A09 research constructor emits the 254-byte generation-19000 CMgr
mass record for one solid made by two positive coaxial rectangular pads.
It takes typed world bounds in metres and a caller-supplied uniform
density in kilograms per cubic metre. The base starts at world XY. The
upper pad meets its top face exactly and has a strictly interior
footprint. The two XY centers must agree to floating-point roundoff.

The constructor derives the combined centroid, volume, mass and
centroidal inertia from both pads. It applies the parallel-axis shifts
and removes both copies of the buried contact from the surface area.
The existing ordinary mass record writer supplies default options and
the world coordinate frame. [Constructor](../../../../../../re/solidworks/WriterResearch/TwoPadMass/CmgrTwoPadMass.py),
[shared mass wrapper](../../../../../../re/solidworks/WriterResearch/CmgrMass.py)

## Sealed native and field-owner replay

The verifier uses the five privately retained discovery saves from
SOLIDWORKS 34.4.1.1011 at capture source
`463a3de14e4cb34aeeaa6aed1aa1e8b2804572c8`. The native audit checks
both owned processes, four healthy controls, all five saved source
hashes and 18 native geometry observations. The strict public SDK
supplies each owned rectangle, blind depth and support transform.
An independent typed Config-0 material walk verifies the cohort's
density of 1,000 kg/m³.
[Licensed source audit and receipt pins](../../SolidWorksTwoPadDiscovery.md),
[verifier](../../../../../../re/solidworks/WriterResearch/TwoPadMass/VerifyCmgrTwoPadMass.py)

The existing CMgr visual, feature and base-header readers reach the
mass record under the matching model allocator and update stamps. The
mass decoder and the following one-body collection opener prove both
record boundaries. The five observed spans are all 1234–1488. The Z
centroid is the third little-endian float64 at offset 1250 in these
files. The codec reaches it through its owner. The pilot had inferred
that offset from the recorded geometry. This replay supplies typed
ownership for the sealed family and leaves the pilot's separate
qualification open.
[Live centroid inference](../../../Supervisor/TwoPadCentroidPilot.md)

All twelve saved physical fields match the newly calculated values
within the existing field-specific tolerances across all five saves.

| Quantity            | Maximum absolute difference |
| ------------------- | --------------------------: |
| Centroid            |              1.74 × 10⁻¹⁸ m |
| Volume              |             1.70 × 10⁻²¹ m³ |
| Surface area        |             8.68 × 10⁻¹⁹ m² |
| Mass                |             1.74 × 10⁻¹⁸ kg |
| Diagonal inertia    |          6.36 × 10⁻²² kg·m² |
| Products of inertia |          3.55 × 10⁻²³ kg·m² |

The 158-byte wrapper matches exactly, with SHA-256
`2e3fc40724bbb867dc41e0340f0b792b83d8b5cdb7254e221473c3ae1d9c73e3`.
Each complete fresh record reads back to the calculated values. Its
analytic zero products differ from the saved kernel residuals. The
verifier also reads back a fresh geometry and density control and
refuses ten contradictory inputs covering placement, dimensions,
density, generation, body count and wrapper state.

```sh
python -B re/solidworks/WriterResearch/TwoPadMass/VerifyCmgrTwoPadMass.py   --run-directory /private/sealed/two-pad-run
```

The five source and generated record rows have aggregate SHA-256
`321a02c2c891e1f6c86b2a355ebddad086fda84866dc516b077779d2b52a94c8`.
Two-pad part construction, the upper sketch's type-14 relation,
A07 admission and licensed generated-part acceptance remain open.
[Automation register](../../../../../Reference/Research/AutomationSteps.md)
