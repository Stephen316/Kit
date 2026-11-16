<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Saved P03 density and derived Fusion mass

The replay reads the exact SOLIDWORKS P03 baseline and three positive XY edits
at capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`. Each source
archive supplies a matching density of 1,000 kg/m³ from its typed Definition
tail and Config-0 material record. The configuration manager supplies the
saved single-solid mass and volume. The configuration manager replay checks
its default mass options and matches the source bounds, volume, and centroid
to the separately reopened SOLIDWORKS observation. [Configuration material](../../Writers/SolidWorks/SolidWorksConfigurationMaterial.md),
[configuration mass](../../Writers/SolidWorksBossCmgrMass.md)

The existing Fusion probe regenerates the exact measured geometry in memory
and verifies the selected perimeter, driver ownership, body history and
geometric mass cache. The packaged material reader resolves the emitted body's
physical asset to `Kit Generic Material` at 1,000 kg/m³. The body and component
have unset mass, density, volume and area overrides. The replay multiplies the
stored geometric volume by the resolved asset density and compares the result,
at full precision, with the saved SOLIDWORKS mass. [Source-derived Fusion Boss probe](FusionSourceBossProbe.md)

| P03 archive | Volume in mm³ | Mass in kg |
| ----------- | ------------: | ---------: |
| Baseline    |         8,000 |     0.0080 |
| Width edit  |         8,200 |     0.0082 |
| Height edit |         9,200 |     0.0092 |
| Depth edit  |         9,600 |     0.0096 |

This is offline evidence for saved uniform density and derived mass on the
four archived shapes. The source and target receipts still need live
measurements for absolute mass and assigned material identity. Licensed
Fusion target acceptance remains open. The replay emits only JSON.
[Licensed witness procedure](FusionSourceBossWitness.md)

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python -B \
  re/Fusion/Reconstruction/DimensionAuthoring/SourceBossConformance.py
```

Two independent Python 3.14 process replays produced normalized JSON SHA-256
`a0f2e9726ef54b6079ba75652d1fa578483ff2a938a9c6aa7bcef9223c92870e`.
