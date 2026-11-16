<!--
This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion native-file research

The maintained [native persistence data model](../../Documentation/Reference/Research/FusionDataModel.md)
consolidates the container, parameter, identity, and B-rep relationships with explicit evidence limits.

Start with the matching feature row. Open its notes and focused test to check
what the saved evidence supports. The [saved-file workflow](Notes/Workflow.md)
covers reproducing checks and [querying the SDK source graph](Notes/Workflow.md#navigate-sdk-source-with-graphify).

## Research reader

Use the explicit research adapter for partial Fusion projections.
See the [reader guide](Notes/SdkReader.md) for history selection, assembly access
and Zstandard support. Strict translation and complete native Fusion output
require further coverage.

## Feature index

| Feature                                                                    | Verified scope and open work                                                                                                   | Decoder                                                                                                         | Focused check                                                                       |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| [Archive, Browser and ACT](Notes/Archive.md)                               | Version-8 framing and qualified manifest routes. Other members and payload fields remain open.                                 | [Source proof](../../src/convert/Formats/Fusion/SourceProof)                                                    | [Wire tests](../../tests/Convert/Formats/FusionCodec)                               |
| [Parameters and formulas](Notes/Parameters.md)                             | Numeric values, bindings and supported formulas. Coverage varies by expression and record layout.                              | [Parameters](../../src/convert/Formats/Fusion/ZipParameters.py)                                                 | [Formula tests](../../tests/Convert/Formats/FusionFormulaTests.py)                  |
| [Timeline and state](Notes/Timeline.md)                                    | Selected history order, groups and feature state. Unknown steps are retained.                                                  | [History projection](../../src/convert/Formats/Fusion/HistoryProjection.py)                                     | [History tests](../../tests/Convert/Formats/FusionHistoryTests.py)                  |
| [Construction geometry](Notes/ConstructionPlanes.md)                       | Qualified offset and angle plane frames in the SDK. The study records additional definitions.                                  | [Plane controls](../../src/convert/Formats/Fusion/ConstructionPlane/PlaneControls.py)                           | [Binding tests](../../tests/Convert/Formats/FusionProof/FusionPlaneBindingTests.py) |
| [Sketches and profiles](Notes/Sketches.md)                                 | Qualified primitives, constraints and profile selections. Other sketch entities and relations remain open.                     | [Sketch projection](../../src/convert/Formats/Fusion/Sketches/SketchProjection.py)                              | [Sketch tests](../../tests/Convert/Formats/FusionSketchTests.py)                    |
| [Extrude](Notes/Extrude.md)                                                | Qualified distance, trimmed and plane-limited solids. Other variants have separate study findings.                             | [Extrude readers](../../src/convert/Formats/Fusion/Extrudes)                                                    | [Public Extrude tests](../../tests/Convert/Api/ApiFusionExtTests.py)                |
| [Revolve](Notes/Revolve.md)                                                | Qualified angular and plane-limited solids, with bounded axis, profile and topology support.                                   | [Revolve readers](../../src/convert/Formats/Fusion/Revolves)                                                    | [Revolve tests](../../tests/Convert/Formats/FusionRevolveTests.py)                  |
| [Scale, Mirror, Shell and Combine](Notes/BodyTools.md)                     | Qualified historical body inputs and supported Scale solids in the SDK. Additional geometry findings are in the study.         | [Body inputs](../../src/convert/Formats/Fusion/BodyInputs)                                                      | [Body input tests](../../tests/Convert/Api/ApiFusionBodyInputTests.py)              |
| [Assemblies](Notes/Assemblies.md) and [bodies](Notes/BodyTopology.md)      | Qualified local occurrences, placement, body ownership and selectors. General history replay remains open.                     | [Assembly](../../src/convert/Formats/Fusion/Assembly) and [topology](../../src/convert/Formats/Fusion/Topology) | [Assembly tests](../../tests/Convert/Api/ApiFusionAssemblyTests.py)                 |
| [Additional feature families](Study/README.md#what-is-currently-recovered) | Saved study findings for patterns, mesh, surfaces and additional solid tools. See each note for supported variants and limits. | [Study reader](Study/decode_basics.py)                                                                          | [Study validators](Notes/Workflow.md#validate-saved-examples)                       |

The [study index](Study/README.md) links saved findings and evidence by topic.
The [corpus notes](Notes/Corpus.md) record import provenance and historical audits.
