# Fusion OGS scene grammar

The two controlled graphics caches are completely decoded into named values. This is evidence for a bounded native graphics codec, not a general OGS implementation. Complete native-document re-emission subsequently passed the native lifecycle checks described below. Field names came from earlier binary inspection, which was removed. The layout is confirmed by complete decoding of both caches and by Fusion accepting byte-identical re-emission. Claims that rest only on binary inspection say so.

| Source | World bytes | Mesh bytes | Simple meshes | World tail | Unaddressed mesh bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| `Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d` | 14,552 | 860 | 10 | 0 | 0 |
| `LocalOracle/RectangleAuthoring/vendor_ProductionCuboid37mm.f3d` | 24,382 | 956 | 14 | 0 | 0 |

`DecodeOgs.py` parses these archives using research archive decompression. It does not load CAD binaries or call production codecs. `DecodedSamples.json.xz` contains every named world field with its exact byte interval and every mesh range with decoded vertices or indices. `EvidenceIndex.json` binds the compressed reports and summarizes coverage.

The sources contain the members `FusionAssetName[Active]/OGS.BlobFolder/OGS/DefaultScene/world` and `stream_mesh_000`. The world describes the scene and references ranges in the mesh streams. A mesh stream is a sequence of typed vertex and index buffers, without an independent record header. Its ranges, formats and lengths come from world metadata.

## Primitive wire values

All fixed-width numbers are little endian except explicitly serialized entity identities. A boolean is one byte, observed as zero or one. Neither a field name nor a type tag is normally stored.

Strings contain a uint32 UTF-16 code-unit length followed by UTF-16LE code units, without a null terminator.

`EntityID` and `ACTEntityID` contain eight bytes in **big-endian numeric order**. Treating these as ordinary little-endian uint64 values consumes the right number of bytes but gives wrong entity identities.

`Qualifier` and `SerializationID` are float64 on disk. The model should retain their numeric role and reject nonintegral or out-of-range values when applying entity/display identity semantics.

`Box3` is six float32 values, `SBox3` six float64 values, and `ADevMatrix` sixteen float32 values. Matrix storage is distinct from the Design segment's double-precision matrix callback.

## Object identity and root dispatch

Objects first write their interface name. Unique objects then write an object identity string that looks like a hexadecimal pointer. A repeated identity writes its interface name and identity but suppresses the body. These are serialized graph identities, not addresses that a reader should dereference.

Worlds and several small geometry values have no object identity string. Group nodes, geometry nodes, text nodes, vertex formats, index buffers and text-style resources do. A generic rule that every interface name is followed by a handle is wrong.

The root world has no trailing `Accelerate` byte, even when its stored interface name is `ARenderList`. Nested `ARenderList` objects use their derived serializer and do have that byte. The old heuristic of reading `Accelerate` whenever the class text says `ARenderList` overruns the complete root by one byte.

A world contains its interface string, `RevisionId:uint32`, `PublishMode:int32`, child objects, and the string `WorldSerializerEndMark`. Nested `ARenderList` adds `Accelerate:bool`; `SingleNodeWorld` adds nothing. These samples use revision 5 and publish mode 1.

## First group and global schema registry

Fusion's first group differs from a generic OGS group. Immediately after its interface and identity comes one schema registry:

1. `Size:uint32`.
2. `Size` pairs of `InterfaceID:string`, `Version:uint32`.
3. `EnvironmentVersion:string`.

The environment string is `RiverRubicon` in both samples; it is a named environment identity, not an unexplained signature. The nine registry entries are `TextureMappingAttribute:1`, `TextureEffectAttribute:1` in the older control and `2` in the saved cuboid, `NodeData:2`, `GraphicsBlobFeatures:1`, `F360InstanceNode:1`, `BillBoardAttribute:2`, `GroupNode:1`, `GraphicsGlobalVersion:1`, `OGSBlobVersion:0`. Registry order is persisted and is retained as an ordered semantic collection.

Every group then writes `HasWorldMatrix` and an optional 16-float matrix; `ClippingPlaneSave`; `StyleGraph`; `LocalGraphicScheme`; `NoCulling` and a float64 world box when culling is enabled; `SaveWorld`; and a conditional world branch. A saved world has `SerializationType:uint32`. Type 0 is a normal optional world link, type 1 is the BRep body callback, and type 3 is the sketch callback. Earlier binary inspection found other branches for T-spline, mesh and lattice bodies; they are not qualified here. The group ends with `NodeDataType:uint32` and the selected quick node-data serializer when nonzero.

## Node-data graph and attributes

The ordinary node-data path writes an interface name, `NodeType:uint32`, a `RenderNode` identity string, and `AttributeType:int32`. The quick path omits the interface and render-node identity but otherwise uses the same field groups.

Attribute type 0 is an empty ordinary attribute set, type 1 an empty extended set, type 2 a populated ordinary set, and type 3 a populated extended set. The complete decode of the samples uses the rule that empty type 1 adds no extended-set payload. It must not be mistaken for a one-element attribute collection.

An ordinary set writes `HasAttributes:uint32`, `mRemoveAttributes:uint32`, `AppendTypeCount:uint32` and appended type IDs, then `AttributeCount:int32`, followed by attribute-name strings and attribute payloads. Each attribute starts with `Priority:int32` and `WinTies:bool`. Its derived field names came from earlier binary inspection. The decoded set includes visibility, selectability, depth priority, transforms, colors, textured/occluded effects, line styles, pixel scaling, billboards, grouping and texture mapping.

An extended set adds `TargetExternalNode:bool`. A true value writes `EntityID:big-endian uint64` and `SegmentID:uint32`; a false value writes `Node:string`. Then `AttributeSetCount:int32` describes nested sets. Each nested set writes `IsTypeAttribute:bool`, an ordinary set, and, for type-specific sets, `ApplyTypeCount:uint32` with its type IDs.

The remaining node-data suffix is:

- `EntityStatus:int32`. Status 1 means `hasEntity`; status 2 means `hasAppendixEntity`. Only those statuses include `SegmentId:uint32` and big-endian `EntityID`. Status 0 includes neither.
- `Qualifier:float64`.
- `ClientTypeNameSaved:bool` and optional client-name string.
- `SubClientTypeNameSaved:bool` and optional subtype-name string.
- `SerializationID:float64`, `DoubleSided:uint32`, `CyclingColor:float32[4]`.
- `ConsolidationFlags:uint32`, `ImmediateConsolidationFlags:int32`, `RenderNodeFlags:uint32`, `SceneInfoFlags:uint32`.

Quick selector 2 is ordinary `NodeData`. Selectors 3, 5, 6 and 7 use the same suffix. Selector 4 is an F360 instance and adds `IsXRef:bool`, conditional big-endian `ACTEntityID`, and `InstanceID:uint32`. These selector rules came from earlier binary inspection. Only the selectors present in the two samples are confirmed by their complete decode.

## Geometry, mesh formats and streams

A geometry node uses the standard render-node framing, including its transform, optional presentation links and ordinary node data. It then writes an optional render geometry, its float64 world box, and an optional effect-instance link. All nonempty optional clipping/style/effect links outside the sampled profile remain unsupported.

Fusion's simple mesh record differs from the generic OGS simple mesh. It holds:

1. Interface name `OgsSimpleMesh`, without an object handle.
2. `Modelbox:float32[6]`, `PrimitiveType:int32`.
3. Vertex-buffer presence boolean. When present: `DynamicResource:bool`, an optional vertex-format link, `StreamCount:int32`, and three `Props:int32` values.
4. Index-buffer presence boolean. When present: the `AIndexBuffer` object and its identity, `DynamicResource:bool`, and four `Props:int32` values, unless already defined.
5. `Planarity:bool`.

Vertex `Props` are stream number, byte offset and byte length. Index `Props` add a boolean-valued integer; false selects uint32 indices, true uint16. Stream files are named `stream_mesh_000` and onward.

A vertex format has an identity and `VertexFormatTableCount:int32`. Each field is six signed 32-bit integers. The roles below came from earlier binary inspection. The complete buffer decode of the samples depends on the element type, usage and offset words. The last three words are zero in every sample, so their roles are not confirmed by a black-box experiment.

| Word | Semantic role |
| --- | --- |
| 0 | Element type enum |
| 1 | Usage enum |
| 2 | Offset in 4-byte words |
| 3 | Vertex stream index |
| 4 | Usage index |
| 5 | Instance control; nonzero semantics remain unqualified |

Observed type 1 is float32x2 and type 2 float32x3. Earlier binary inspection named usage 0 `POSITION`, 1 `NORMAL`, and 2 `TEXCOORD0`; those names are not confirmed by a black-box experiment.

The sampled formats are position-only triples and interleaved position/normal/texture-coordinate octuples. Their stream index, usage index and instance control are all zero. The decoded buffers cover every stream byte; there is no unexplained padding. Buffer offsets and allocation order remain semantic storage descriptors rather than a license to carry original bytes forward.

The saved cuboid has four additional 24-byte position-only sketch-line buffers, accounting for its 96 additional mesh bytes. Its body display branch references BRep entities through node data and bounds; its 12 edge and 6 face LOD masks are zero. The remaining buffers describe origin/work geometry. No inference that all Fusion body tessellation is absent follows from this sample.

## BRep and sketch callbacks

Type-1 group worlds hold `ValidBody:bool`; when true, a quick body-child group for edges, `EdgesCount:uint32` and edge LOD nodes, another body-child group for faces, `FacesCount:uint32` and face LOD nodes. Finally `HasModelBox:bool` controls a **float64** box. Quick body-child groups contain transform and presentation flags followed by node data; they omit the ordinary group world and culling fields.

Each body LOD node contains `NodeDataType`, quick node data, `HasLODs:uint32`, an optional render payload, a float64 world box and `UseClosestLOD:bool`. The populated sampled masks contain one set bit. A populated mask adds `DisplayItemType:uint32`; selector 0 uses an optional ordinary render-geometry link. Nonzero display-item serializers are outside this sample profile. Earlier binary inspection said each mask is `1 << level`, with a fallback level 11. The samples only show one-bit masks; the rule is not otherwise confirmed by a black-box experiment.

Type-3 group worlds hold `HasFaces:bool` and optional BRep-body callback, `LODGeoNodeCount:int32`, `RegularNodeCount:int32`, the LOD nodes and regular optional links, then `NoCullingNodeCount:int32` and its links. The saved cuboid has nine LOD nodes, zero regular nodes and zero nonculling nodes. Five sampled LOD payloads are `FatPointMesh`, consisting of its class string, `Width:int32`, `Height:int32`, and `BBoxSize:float32[3]`; the four remaining payloads are simple line meshes. The last sketch attribute, `HWSelectionPostProcessingAttribute`, has no derived bytes in the samples.

## Texture cache and text

`TextureMappingAttribute` adds a saved-reference flag, asset-name string, segment ID and big-endian entity ID, then `TextureMappingCache`. That cache contains `CacheIsLayered:bool`, primary cache data, `CacheHasSecondary:bool`, and optional secondary data.

Each cache data record has `Mode:int32`, `Axis:float64[3]`, `BBox:float64[6]`, `BakedTfm:float64[16]`, and `MappingTfm:float64[16]`. Mode 6 adds procedural-wood origin and board-face-axis triples. The saved cuboid uses primary mode 0 and secondary mode 6. Earlier binary inspection said mode 4 adds two cylindrical-cap booleans; that is not confirmed by a black-box experiment. These are named values even when zero or otherwise unused by the active material.

`FTextNode` records use text-node framing. Standard render-node framing precedes a float32 world matrix, a two-float envelope, optional text, global alignment and escapement, optional text/paragraph/block-style resources, then anchor point and priority. Style fields are native font, color, spacing, alignment, indentation and baseline properties. The sampled paragraph tab-stop lists are empty; nonempty lists are not admitted by this decoder. Resource identity reuse is retained.

## Qualification and remaining work

Both sampled world streams and all mesh bytes are consumed. The production semantic codec subsequently regenerated both world/mesh pairs byte-identically as part of complete ReadDocument → EmitParsed archive reconstruction. Fusion 2706.1.17 accepted both complete reconstructed archives and their original controls through initial geometry/material/appearance/mass inspection, rollback, restore, rebuild, height editing, save and reopen. See ../../LocalOracle/NativeDocuments/Preparation.json and NativeAcceptance.json. This establishes the recorded profile and lifecycle, without claiming a pixel-level image comparison or other native callbacks.

The profile must reject unsupported class names, registry versions, nonempty clipping/style/effect links, nonzero display-item serializers, unsupported mesh formats/instancing, nonempty paragraph tab stops, and regular/nonculling sketch-node branches until their complete contracts are promoted. The native type-2, type-4/5 and type-6 group-world branches remain outside the qualified BRep/sketch profile. No residual spans, original graphics byte buffers, or installed-library calls may enter production.

No additional native capture is required to promote the two solved controls. Later expansion should capture one changed rendering variable at a time: nonempty paragraph tabs, nonempty style/clipping links, populated body tessellation LODs and instanced vertex streams. Each control should check one field family by complete decoding, not by size matching alone.
