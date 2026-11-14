# Production Fusion document and entity codecs

## Behavior

Kit can now author a complete native F3D document from an immutable semantic specification using production Python modules. `EmitDocument` allocates fresh identities, builds the Design feature graph and ACT/Browser relationships, and serializes versioned entity metadata and bulk records. `EmitDocument` also emits cylinder topology and its modeling journal, and writes root/asset manifests, previews, and required ZIP directories.

The writer reads no source archive, captured entity graph, donor geometry, research module, or runtime CAD library. The packaged JSON contains declarative class, inheritance, member, and wire-type vocabulary; it contains no saved entity values or archive payloads.

The initial document profiles are a parameter-only design, one circular sketch, and a circular sketch with a dependent solid extrusion. The [rectangle and cuboid extension](FusionRectangleAuthoring.md) and [tapered circular extrusion extension](FusionTaperedDocuments.md) document the additional profiles and their separate acceptance boundaries. Length and radius are specified in millimeters. Parameter, sketch, extrusion, and body names are explicit inputs. Geometry and timeline identities are allocated consistently across feature recipes, body history, browser references, and the embedded BRep journal.

## Usage

```python
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec

Specification = DocumentSpec(
    Title="Native cylinder",
    ParamName="height",
    LengthMm=17.25,
    ProfileKind="extrusion",
    RadiusMm=12.5,
)
Path("Cylinder.f3d").write_bytes(EmitDocument(Specification))
```

Use the repository's supported Python environment. The production entry point does not launch Fusion. The separate research acceptance launcher uses `uv run --no-sync python re/Fusion/Reconstruction/DocumentAuthoring/ProductionAcceptance.py --output /tmp/Cylinder.f3d --profile extrusion` to generate an artifact for an explicitly authorized native application session.

`ReadDocument(Payload)` returns immutable document, segment, entity, and body-history models for this qualified document profile. `EmitParsed(Model)` serializes those values. All three entity segments and the complete supported BRep history are decoded; retained source bulk or history payloads are not inputs to re-emission. Unknown package parts and unsupported geometry profiles are rejected.

`BrepCodec.ReadHistory` recovers cylinder dimensions, identity and topology tags, the exact header, and the complete two-state insertion journal. `ReadSnapshot` recovers the cylinder and two planar selection bodies. Both consume every topology, attribute, reference, and journal token; a graph bijection admits differing record allocation order. Readers also preserve typed vertex edge indices independently from topology record ordinals. The admitted geometry header is version 23200 with the documented scale and tolerances, and other topology/journal layouts are rejected.

## Lower-level contracts

`EntityCodec.DecodeEntities` and `EncodeEntities` translate physical `BulkRecord` objects to and from immutable `EntityRecord` values using an explicit `EntityProfile` and the archive's `MetaClass` declarations. The model retains primary/continuation framing, inheritance ownership, root IDs, observer subjects, named metadata, typed values, collection order, and local/external references. Reference targets must exist and satisfy declared target-class constraints. Unknown classes, mismatched schema versions, unconsumed payload bytes, malformed ownership, and incompatible references are rejected.

`ContainerCodec.ReadContainer` and `EmitContainer` operate on typed document and asset manifests, segment streams, previews, parts, and empty directories. The supported envelope has one active asset and Design, ACT, and Browser segments. It verifies manifest identity relationships, stream headers, member paths, primary identity order, and complete member accounting. Stored output includes the explicit directory entries required by native segment and BRep lookup.

`BuildAssembly` and `BuildBrowser` construct auxiliary graphs from the authored Design result. Browser relationship entries target the constraints collection, and observer indices account for the existing Design subjects. These are semantic graph builders, not payload patches.

## Native verification

Fusion 2706.1.17 accepted the [complete production-authored document](../../../re/Fusion/LocalOracle/Authored/ProductionExtrusion.f3d), SHA-256 `5645020130771517c674eac3854c2d96c00100e9bb277e353f87f35295a3d995`. The [native report](../../../re/Fusion/LocalOracle/Authored/ProductionDocumentAcceptance.json) records:

- Correct initial 17.25 mm height and 8.467573949129104 cm³ volume before recomputation.
- Two healthy timeline features, one solid, three faces, two edges, and two vertices.
- Rollback to sketch-only state and restoration of the initial solid.
- Successful full recomputation.
- A parameter edit to 23 mm with volume 11.290098598838801 cm³.
- Native save/reopen retaining the edited dimensions and healthy history.
- Zero documents left open by acceptance.

The separately promoted parameter and circle profiles also pass native editing and save/reopen, recorded in [parameter acceptance](../../../re/Fusion/LocalOracle/Authored/ProductionParameterAcceptance.json) and [circle acceptance](../../../re/Fusion/LocalOracle/Authored/ProductionCircleAcceptance.json). The complete reader/re-emitter reconstructs all 213 physical entity records across the three segments and the typed history. The reader/re-emitter produces exactly the same 61,439-byte archive and SHA-256; [the reconstruction report](../../../re/Fusion/LocalOracle/Authored/ProductionReemitted.json) records the boundary.

A subsequent [semantic comment edit](../../../re/Fusion/LocalOracle/Authored/ProductionEdited.json) changes the decoded user-parameter comment and re-emits every entity and BRep history field. [Native acceptance](../../../re/Fusion/LocalOracle/Authored/ProductionEditedAcceptance.json) confirms the changed comment on open and after save/reopen, alongside correct initial geometry, rollback, and a later 23 mm parameter rebuild. This exercises an actual typed-model mutation, not only byte equality.

A native-source history reconstruction also passes open, rollback, recomputation, 7-to-23 mm editing, and save/reopen. The [native history report](../../../re/Fusion/LocalOracle/Authored/NativeHistoryAcceptance.json) qualifies preserved vertex indices `(2, 0)`; [the vertex-index gotcha](../../Gotchas/Conversion/Fusion/FusionVertexEdgeIndices.md) records why geometry equivalence does not permit discarding this state.

The saved native archive digest is `fcce745b873b6758ebd72cd25c1dbef72004f6b028ad4e95974a10b32b0aa3b9`. An earlier [production-container acceptance](../../../re/Fusion/LocalOracle/Authored/ProductionContainerAcceptance.json) isolates the container encoder from the subsequent complete production graph promotion.

Integration cases exercise native archive decoding and complete stream reconstruction, typed named-metadata edits, target-class rejection, complete container reconstruction, and auxiliary graph emission/reparse. Automated tests run only in PR CI; native acceptance is a separate measured application boundary.

## Limits and related evidence

This release qualifies the stated document profiles. Arbitrary feature synthesis, external-document assemblies, drawings, sculpt/T-spline data, and historical schemas need separate semantic and native acceptance. The full [corpus Design decoder](FusionCorpusEntityCoverage.md) has broader structural coverage than the independently generated document profiles. It does not expand this writer's acceptance claim.

The [entity model](../../../re/Fusion/Reconstruction/EntityGraph/DataModel.md), [extended callbacks](../../../re/Fusion/Reconstruction/EntityGraph/ExtendedCallbacks.md), [independent authoring specification](../../../re/Fusion/Reconstruction/DocumentAuthoring/README.md), [container model](../../../re/Fusion/Reconstruction/ContainerAuthoring/ContainerModel.md), and [BRep history model](../../../re/Fusion/Reconstruction/BrepHistory/HistoryAuthoring.md) provide field-level evidence. The [directory](../../Gotchas/Conversion/Fusion/FusionArchiveDirectories.md), [Browser role](../../Gotchas/Conversion/Fusion/FusionBrowserEntityRoles.md), and [geometry cache](../../Gotchas/Conversion/Fusion/FusionGeometryCaches.md) gotchas explain why a valid ZIP or readable parameter graph alone does not establish a usable native design.
