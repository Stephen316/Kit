# Complete circular sketch graphics

The typed graphics reader/writer now handles the saved scene in native circle sketches, circular extrusions and tapered circular extrusions. `ReadDocument` and `EmitParsed` reconstruct the complete archive, including the original graphics world and mesh streams. The public adapter projects these native documents separately through [the reference-driven circular contract](../Adapter/FusionNativeCircularProjection.md).

## Wire model

`SketchWorld.RegularNodes` and `SketchWorld.NoCullingNodes` preserve the two explicit signed-count link arrays after the body LOD list. Their default is an empty tuple for existing in-memory callers. Null links retain their serialized presence bit. A linked node can be a shared ordinary node or an inline `PrimitiveLod`.

`PrimitiveLODGeometryNode` is an inline serializer. Its fields are node-data selector/payload, unsigned single-LOD mask, and an optional shared `SimpleMesh` resource when that mask is nonzero. The remaining fields are six double-precision world bounds, closest-LOD flag and an optional shared `CircleArc<double>` primitive. The ordinary LOD path does not contain the body-specific `DisplayItemType` word. In contrast, `SimpleMesh`, `VertexBuffer` and `CircleArc<double>` use explicit resource handles and preserve shared identity.

`RenderMesh` differs from the existing Fusion-specific `OgsSimpleMesh` model. It stores six float32 model bounds, a vertex-format reference, signed primitive type and an optional vertex-buffer resource. `RenderMesh` also stores a signed index-save flag followed by the optional index resource. The save flag is derived from the typed index reference and accepts only zero or one; a set flag with an absent link fails. Mesh indices must address the explicit vertex allocation, and vertex-buffer and mesh format references must agree.

`CircleArcValue` contains a signed sampling count, double-precision parameter interval, radius, center, normal, start/end angles and reference point. The reference point is the center plus the radius-scaled reference direction, not a direction vector. These twelve doubles follow the curve-base sampling and interval fields; the initial integer is not an opaque payload size. Positive radius/sampling and ordered parameter interval are required for this qualified profile.

`TransparentLayerAttribute` adds its signed layer type. `FOccludedFatPointEffectAttribute` composes color, optional image/path, two float32 point-size values and visible/occluded opacity. Both retain the common attribute priority and tie-breaking flag. Unknown attributes, node classes, mesh classes and analytic primitives remain explicit errors.

## Evidence and verification

Binary inspection first supplied the serializer constructors and resource-flag decisions. That evidence was removed at the tip. The exact reconstruction and native acceptance below are the black-box evidence for this profile. The [framing gotcha](../../../Gotchas/Conversion/Fusion/Graphics/FusionInlineGraphics.md) explains the independent class-name, object-handle and body-inline boundaries.

[Preparation](../../../../re/Fusion/LocalOracle/RotationalDocuments/Preparation.json) produced three complete archives. The native circle has 44 shared objects; cylinder and frustum have 43 each. The graphics world and every graphics stream reconstruct exactly for all three. The circle archive's entire uncompressed member set is byte-exact. Cylinder/frustum may canonically regenerate geometry/material members while retaining their typed semantics.

[Native acceptance](../../../../re/Fusion/LocalOracle/RotationalDocuments/NativeAcceptance.json), SHA-256 `5950746b0d3601bcf3cb7bf798288aa5a894e2d410e875018ab67f0d95a62d1f`, passed all three original controls and all three re-emissions in Fusion 2706.1.17. The native lifecycle compared initial load, every timeline rollback, restoration/rebuild, edits, save and reopen. `publicHeight` changed 21→26 mm in each document, the sketch-only radius changed 14→16 mm, and the frustum taper changed −3→4°. Edited cylinder/frustum volumes were 11.762122895039681 and 13.634178374871233 cm³; both retained three faces, two edges and two vertices. All feature health and measured values matched their controls. Zero documents remained open.

Six new remote archive-boundary cases cover exact graphics reconstruction in all three documents and rejection of unknown world, analytic-primitive and render-mesh classes. Existing general-document and public API cases also cross this path. Black, Ruff, mypy, strict Pyright and steering checks passed the production graphics scope. No local tests ran; the new cases await PR CI.

This qualification does not add arbitrary LOD sets, every analytic graphics primitive, image resources, arbitrary native feature projection or generic callback serialization. It does not imply that a render mesh replaces authoritative BRep or parametric history.
