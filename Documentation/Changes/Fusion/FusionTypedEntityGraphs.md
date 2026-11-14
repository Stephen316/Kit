# Typed Fusion entity graphs and independently authored geometry history

## Behavior

The research graph codec now reads and re-encodes every indexed Design record in the controlled circle, 7 mm extrusion, and 13 mm extrusion archives.
The total is 824 records and 75,675 payload bytes, with no unexplained suffixes.
It interprets inherited schema groups, subjects, named metadata, cross-segment and named-root references, generic containers, nested material/mass values, geometry callbacks, and the observed recipe callbacks.
The [coverage summary](../../../re/Fusion/Reconstruction/EntityGraph/GraphSummary.json) binds the source archives, reflection catalog, counts, and compressed field evidence.
The [entity data model](../../../re/Fusion/Reconstruction/EntityGraph/DataModel.md) documents each framing layer and the native semantic comparison.

The research API `read_graph(Path)` returns typed record values and their exact schema context; `emit_record(Codec, Value, IsPrimary)` receives those values rather than a retained source payload.
The codec remains research code: it reads the captured schema vocabulary, and three recipe callback members have established widths and offsets but incomplete semantic names.
Byte-exact reconstruction does not erase those remaining interpretation gaps.

Separate generators author both embedded geometry members from cylinder dimensions, sketch/profile topology, explicit identity relationships, and journal state inputs.
The solved `.smbh` contains 35 newly allocated records and an insertion journal.
The snapshot `.smb` contains 59 newly allocated records for the cylinder and two planar profile bodies.
Neither generator reads a native geometry payload.
See [history authoring](../../../re/Fusion/Reconstruction/BrepHistory/HistoryAuthoring.md), [snapshot authoring](../../../re/Fusion/Reconstruction/SnapshotAuthoring/SnapshotDataModel.md), and the [BRep data model](../../../re/Fusion/Reconstruction/BrepDataModel.md).

## Native verification

The [full geometry rewrite](../../../re/Fusion/LocalOracle/Features/FullBrepRewrite.json) reconstructs all 289 Design records, installs both independently generated geometry members, and omits the controlled document's OGS graphics caches.
[Fusion acceptance](../../../re/Fusion/LocalOracle/Features/FullBrepAcceptance.json) establishes:

- Initial 19 mm height and `5.969026041820864` cm³ volume before `computeAll()`.
- Both sketch and extrusion healthy, with no warning or error message.
- Rollback to one sketch and zero modeled bodies, then restoration of the 19 mm solid.
- A subsequent parameter edit to 23 mm, rebuild, native save and reopen with correct geometry and healthy features.
- Zero open documents remaining after the acceptance run.

The existing Design mass-cache values were not patched; the observed native body measurements were correct after loading the new geometry. That observation does not establish the internal invalidation algorithm.
This is a same-source document rewrite with independently authored geometry, not a wholly independent F3D document: material, manifest and other surrounding source members remain.
Production adapter discovery stays disabled.

## Archive envelope research

The [envelope model](../../../re/Fusion/Reconstruction/DocumentEnvelope/EnvelopeRecipe.md) fully decodes the controlled root/asset manifests and ACT/Browser records.
It additionally identifies the nested material store's block allocator, TOC and definition schemas.
The subsequent [material serialization entry](Materials/FusionMaterialSerialization.md) completes the controlled instance values and records native package acceptance.
Verbose generated evidence is retained in digest-indexed compressed archives, while interpretation and native acceptance reports remain readable.

See the [custom value order gotcha](../../Gotchas/Conversion/Fusion/FusionCustomValuePersistence.md), [material padding gotcha](../../Gotchas/Conversion/Fusion/FusionMaterialStorePadding.md), and [graphics cache omission evidence](../../Gotchas/Conversion/Fusion/FusionGraphicsCacheOmission.md).
General automated tests remain PR-only; these new observations came from research decoding and explicitly authorized application acceptance.
Static native-code analysis also informed them; it was removed at the tip and is not a black-box confirmation.
