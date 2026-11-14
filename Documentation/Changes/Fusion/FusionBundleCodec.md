# Fusion bundle envelope codec

## Behavior

`BundleCodec` reads and writes the qualified Fusion `.f3z` envelope profile.
Immutable models expose document identities, graph roots, typed reference groups, role metadata, and document members.
The codec handles one closed design graph with description version `0.1`.

`ReadBundle` validates ZIP framing, bounded JSON, exact member ownership, unique identities, and graph references.
It rejects cycles, unreachable documents, duplicate JSON keys, unsafe member names, unknown fields, and unsupported packaging variants.

`EmitBundle` derives JSON and ZIP framing from typed values.
Callers supply each complete serialized F3D or F2D document through `BundleFile`.
Document payloads remain byte-exact. Outer compression and JSON whitespace can change.
The bundle layer does not claim to decode or convert a member's parametric or drawing content.

## Usage

Import the public functions from their defining modules:

```python
from convert.formats.Fusion.BundleCodec.EmitBundle import EmitBundle
from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle

Bundle = ReadBundle(SourceBytes)
OutputBytes = EmitBundle(Bundle)
```

`SourceBytes` must contain the complete supported F3Z archive.
The same read/re-emit API generated the artifact used for the explicitly authorized native acceptance session.
Callers can also construct `FusionBundle` from typed descriptions and independently authored document bytes.

The reader accepts an optional `InflateZstd` callback for compatible compressed members.
The emitter uses the existing deterministic ZIP writer and requires no CAD runtime.

## Limits

The maximum archive size is 128 MiB, with at most 4094 documents.
Each document is limited to 64 MiB. Each JSON envelope is limited to 4 MiB.
JSON depth is limited to 32, with at most 100,000 nodes and 1 MiB per string.

The qualified profile rejects multiple graphs, external `designObjectRefs`, sharing descriptors, and secondary object packaging.
Application-specific metadata remains typed text. The codec preserves embedded JSON strings without interpreting their application semantics.
Nested document validation remains the relevant document codec's responsibility.

F3D XREF bundles have supplied corpus evidence.
F2D and DERIVED envelope tags follow the upstream specification but lack supplied native acceptance evidence.

## Verification

Raw research inspection found nine F3D documents and eight XREF links in the supplied bundle.
All seventeen repeated document identities match their description records.
All eight role links match the root document's `RedirectionsStream.dat`.

Integration coverage crosses the existing ZIP reader, typed bundle codec, nested redirection stream, and ZIP writer boundaries.
It covers complete document preservation and rejects missing targets and unindexed members.
Tests were not executed locally. All three bundle compatibility cases passed in remote run `43221337105`; the broader suite had 21 unrelated sketch-tag qualification failures. Native upload acceptance is recorded separately below.
Black, steering compliance, Mypy, Ruff, and Pyright passed for all 32 new production and integration Python files.
Pyright reported three existing unrecognized configuration settings and no code errors or warnings.

See the [detailed bundle data model](../../../re/Fusion/Reconstruction/BundleAuthoring/BundleDataModel.md)
and [inspection evidence](../../../re/Fusion/Reconstruction/BundleAuthoring/BundleEvidence.json).

## Native import

The public archive import API accepts F3D only.
F3Z acceptance requires an asynchronous upload through `DataFolder.uploadFile`.
See [the F3Z import boundary](../../Gotchas/Conversion/Fusion/FusionBundleUpload.md) and [optional active-project selection](../../Gotchas/Conversion/Fusion/FusionActiveProjectSelection.md).

## Measured native acceptance

Fusion 2706.1.17 accepted the [production-reconstructed bundle](../../../re/Fusion/LocalOracle/Bundles/kit_production_example1.f3z), SHA-256 `33a42876f25ecc72844cf37af3ab35cb17ed6bfe621ff4e21ce4b3a62c6afe54`. The [preparation manifest](../../../re/Fusion/LocalOracle/Bundles/Preparation.json) records all source-document digests. The writer reconstructed the JSON and ZIP envelope and preserved each complete input document; it did not independently regenerate those nine nested designs.

The [native report](../../../re/Fusion/LocalOracle/Bundles/NativeBundleAcceptance.json) records all nine documents uploaded into a new isolated acceptance project, all eight root references resolved, and successful root opening. The root has 87 timeline entries, 24 top-level occurrences, 160 total occurrences, 21 components, and 39 component-owned BRep bodies.

Full native recomputation produced no feature warnings or errors. A newly created acceptance parameter was edited from 2 mm to 4 mm and saved as cloud version 2. The parameter was then reopened with the value and all eight references intact. The structural counts remained unchanged. The session closed all documents it opened. The acceptance project remains available for inspection; it was not deleted.

The upload future initially returned a child document rather than the graph root. [The upload-result gotcha](../../Gotchas/Conversion/Fusion/FusionBundleUploadResult.md) records the required root-selection check. A timeline group reports the unknown health enum without an error; [the group-health gotcha](../../Gotchas/Conversion/Fusion/FusionTimelineGroupHealth.md) distinguishes that state from feature failures.
