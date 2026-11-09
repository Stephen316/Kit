<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion native-file research

Start with the matching feature row. Open its notes and focused test to check
what the saved evidence supports. The [saved-file workflow](Notes/Workflow.md)
covers reproducing checks and [querying the SDK source graph](Notes/Workflow.md#navigate-sdk-source-with-graphify).

## Public SDK reader

Use `open_document("part.f3d", strict=False)` for the SDK's partial projection.
See the [reader guide](Notes/SdkReader.md) for history selection, assembly access
and Zstandard support. Strict translation and complete native Fusion output
require further coverage.

## Feature index

| Feature                                                                    | Verified scope and open work                                                                                                   | Decoder                                                                                                         | Focused check                                                                       |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| [Archive, Browser and ACT](Notes/Archive.md)                               | Version-8 framing and qualified manifest routes. Other members and payload fields remain open.                                 | [Source proof](../../src/convert/formats/Fusion/SourceProof)                                                    | [Wire tests](../../tests/convert/formats/FusionCodec)                               |
| [Parameters and formulas](Notes/Parameters.md)                             | Numeric values, bindings and supported formulas. Coverage varies by expression and record layout.                              | [Parameters](../../src/convert/formats/Fusion/ZipParameters.py)                                                 | [Formula tests](../../tests/convert/formats/FusionFormulaTests.py)                  |
| [Timeline and state](Notes/Timeline.md)                                    | Selected history order, groups and feature state. Unknown steps are retained.                                                  | [History projection](../../src/convert/formats/Fusion/HistoryProjection.py)                                     | [History tests](../../tests/convert/formats/FusionHistoryTests.py)                  |
| [Construction geometry](Notes/ConstructionPlanes.md)                       | Qualified offset and angle plane frames in the SDK. The study records additional definitions.                                  | [Plane controls](../../src/convert/formats/Fusion/ConstructionPlane/PlaneControls.py)                           | [Binding tests](../../tests/convert/formats/FusionProof/FusionPlaneBindingTests.py) |
| [Sketches and profiles](Notes/Sketches.md)                                 | Qualified primitives, constraints and profile selections. Other sketch entities and relations remain open.                     | [Sketch projection](../../src/convert/formats/Fusion/Sketches/SketchProjection.py)                              | [Sketch tests](../../tests/convert/formats/FusionSketchTests.py)                    |
| [Extrude](Notes/Extrude.md)                                                | Qualified distance, trimmed and plane-limited solids. Other variants have separate study findings.                             | [Extrude readers](../../src/convert/formats/Fusion/Extrudes)                                                    | [Public Extrude tests](../../tests/convert/api/ApiFusionExtTests.py)                |
| [Revolve](Notes/Revolve.md)                                                | Qualified angular and plane-limited solids, with bounded axis, profile and topology support.                                   | [Revolve readers](../../src/convert/formats/Fusion/Revolves)                                                    | [Revolve tests](../../tests/convert/formats/FusionRevolveTests.py)                  |
| [Scale, Mirror, Shell and Combine](Notes/BodyTools.md)                     | Qualified historical body inputs and supported Scale solids in the SDK. Additional geometry findings are in the study.         | [Body inputs](../../src/convert/formats/Fusion/BodyInputs)                                                      | [Body input tests](../../tests/convert/api/ApiFusionBodyInputTests.py)              |
| [Assemblies](Notes/Assemblies.md) and [bodies](Notes/BodyTopology.md)      | Qualified local occurrences, placement, body ownership and selectors. General history replay remains open.                     | [Assembly](../../src/convert/formats/Fusion/Assembly) and [topology](../../src/convert/formats/Fusion/Topology) | [Assembly tests](../../tests/convert/api/ApiFusionAssemblyTests.py)                 |
| [Additional feature families](Study/README.md#what-is-currently-recovered) | Saved study findings for patterns, mesh, surfaces and additional solid tools. See each note for supported variants and limits. | [Study reader](Study/decode_basics.py)                                                                          | [Study validators](Notes/Workflow.md#validate-saved-examples)                       |

The [study index](Study/README.md) links saved findings and evidence by topic.
The [corpus notes](Notes/Corpus.md) record import provenance and historical audits.
