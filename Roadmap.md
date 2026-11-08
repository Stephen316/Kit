<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Kit completion roadmap

The initial app-wide estimate is **20 of 100 points** at baseline commit
`9e1c6b60`. This is a coverage score based on repository evidence. It gives
equal weight to CAD families, although their remaining engineering effort
will vary. Keep the denominator fixed across feature and format milestones.
The current estimate is **22 of 100 points** after Kit gained a verified
subset of local Fusion assembly reads.

The scope includes all nine CAD families named in the [README](README.md)
plus the shared SDK. The public adapter catalog at the baseline returns
`solidworks.sldprt`, `freecad.fcstd`, `catia.v5`, and `interchange.json`.
CATIA has a registered adapter and remains on the roadmap for broader native
support. Parashell appears in the supported list and needs a concrete format
contract and a public adapter path. JSON is part of the shared SDK score.

## Format coverage

Each column is worth two points per family. Score **0** when evidence for
the checkpoint is missing, **1** for a demonstrated subset, and **2** when
the agreed format and version scope passes the full checkpoint. Reader
research can earn partial read credit. Reversible carriers and byte replay
alone earn no native write credit.

| CAD family          | Native read | Native write | Geometry and editable history | Assemblies | Strict conversion with target validation |      Points |
| ------------------- | ----------: | -----------: | ----------------------------: | ---------: | ---------------------------------------: | ----------: |
| SOLIDWORKS          |           1 |            1 |                             1 |          1 |                                        1 |           5 |
| Parashell           |           0 |            0 |                             0 |          0 |                                        0 |           0 |
| FreeCAD             |           1 |            1 |                             1 |          1 |                                        0 |           4 |
| Fusion              |           1 |            0 |                             1 |          1 |                                        0 |           3 |
| CATIA               |           1 |            0 |                             1 |          1 |                                        0 |           3 |
| NX                  |           0 |            0 |                             0 |          0 |                                        0 |           0 |
| Rhino               |           0 |            0 |                             0 |          0 |                                        0 |           0 |
| Creo                |           0 |            0 |                             0 |          0 |                                        0 |           0 |
| AutoCAD             |           0 |            0 |                             0 |          0 |                                        0 |           0 |
| **Format subtotal** |             |              |                               |            |                                          | **15 / 90** |

- SOLIDWORKS has native part reconstruction for controlled feature families
  and a typed assembly core. The recorded strict FreeCAD-to-SOLIDWORKS
  structural audit accepted 44 of 165 files and zero of five assemblies.
  Selected generated parts were edited and rebuilt in SOLIDWORKS.
  [Corpus and oracle evidence](re/solidworks/CorpusCoverage.md)
- FreeCAD has native archive, geometry, feature, and assembly paths with
  fixture coverage. Its isolated recompute test requires a configured oracle.
  The baseline assigns zero strict verification credit pending recorded
  results for the agreed conversion routes.
  [FreeCAD checks](tests/convert/freecad)
- CATIA reads part and assembly containers and exposes a subset of geometry,
  feature, and assembly data. The overlay tests explicitly identify limits
  of modified outputs. [CATIA checks](tests/convert/catia)
- Fusion is discoverable in the SDK as the read-only `fusion.f3d` adapter.
  It requires explicit opt-in to the partial read and projects linked
  distance Extrude definitions, plane-limited Revolve definitions, and
  source-derived Extrude and Revolve solids for verified subsets. Sixteen captures from Fusion 2705.1.30
  and 2706.1.17 matched saved body geometry and passed Kit JSON round-trips.
  The SDK also reads local assembly definitions, occurrences, placements, and
  saved component body inventories. Broader geometry and assembly coverage, the native writer,
  and strict conversion remain open. [Fusion evidence](re/Fusion/README.md)

## Shared SDK

| Checkpoint                                | Baseline evidence and remaining verification                                                                                                        |     Points |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ---------: |
| Registry and public conversion API        | Catalog, discovery, and conversion entry points with contract tests.                                                                                |          2 |
| Neutral document and JSON interchange     | Model validation, serialization, and reversible JSON round trips with fixture tests.                                                                |          2 |
| Strict transfer and loss reporting        | Strict rejection and attestations exist. Full coverage requires target-verified preservation across the conversion matrix.                          |          1 |
| Packaging and runtime isolation           | Wheel configuration and runtime isolation checks exist. Full verification covers all supported releases and environments.                           |          1 |
| Documentation and reproducible validation | Usage and research guides exist. Full coverage requires a supported format and version matrix and reproducible verification for every listed route. |          1 |
| **Shared subtotal**                       |                                                                                                                                                     | **7 / 10** |

[Public API tests](tests/convert/api) · [Interchange tests](tests/interchange) ·
[Runtime isolation tests](tests/convert/runtime) · [End-to-end workflow](.github/workflows/EndToEnd.yml)

## Verification gates

For each CAD family, record the file types, version ranges, fixture sources,
and feature and assembly capabilities covered before awarding full credit.
Exercise readers and writers through the public SDK. Cover geometry, editable
feature trees, assemblies, and failure cases using representative fixtures.
For strict routes, verify independently in the destination application that
generated files open, rebuild, remain editable, and preserve the required
source data. Use isolated CAD applications as test oracles. Include both
conversion directions between each pair where their capabilities overlap and
verify explicit rejection where strict preservation is impossible.

Run the SDK workflow and packaging checks against the final versions of the
adapters. Record the exact revisions, fixture counts, oracle versions, and
outcomes that support score changes. An intermediate feature result can
improve the coverage score while its parent checkpoint remains partial.
