# Driven sketch dimensions: complete controlled graph delta

## Evidence boundary

This model describes the horizontal and vertical point-to-point dimensions created by the native capture script [CaptureRectangleDimensions.py](../../LocalOracle/CaptureRectangleDimensions.py), in Fusion 2706.1.17. It is a read-only interpretation of saved Design graphs. It does not establish an independently authored dimensional sketch or a general sketch solver.

[InspectDimensions.py](InspectDimensions.py) uses only the research entity decoder and reads all four archives. [DimensionGraphs.json.xz](DimensionGraphs.json.xz) retains every decoded frame and inheritance group, exact class/version/member declarations, and every changed field. [DimensionSummary.json](DimensionSummary.json) records source and evidence digests. No product codec, native application call or local test was executed by this analysis.

| Stage | Physical records | Primary entities | Decoded payload bytes | Native operation |
| --- | ---: | ---: | ---: | --- |
| Baseline | 256 | 232 | 24,069 | Rectangle and two user parameters |
| WidthDimension | 262 | 236 | 25,062 | Add horizontal dimension, expression `controlledWidth` |
| WidthDepthDimensions | 268 | 240 | 26,055 | Add vertical dimension, expression `controlledDepth` |
| EditedDimensions | 268 | 240 | 26,055 | Change inputs from 17×23 to 19×29 mm and rebuild |

All 1,054 physical records, totaling 101,241 payload bytes, were fully consumed with no unexplained tails. The archive digests are recorded in the summary and match the native [Capture.json](../../LocalOracle/RectangleDimensions/Capture.json).

The source has sketch `202`, DcSketch feature `207`, parameter table `16`, name helper `17`, Design fragment `26`, node group `27`, compute manager `28` and dependency manager `29`. Corner points are A=`228`, B=`230`, C=`232`, D=`234`; line entities AB/BC/CD/DA are `236/237/238/239`. These are observed joins, not required authoring IDs.

## One dimension adds four logical entities

| Role | Width | Depth | Primary class/version |
| --- | ---: | ---: | --- |
| Sketch dimension | 245 | 255 | `FusionSketchLinearDim` v3 |
| Model parameter | 246 (`d3`) | 256 (`d4`) | `Parameter` v10 |
| Design-capture binding | 247 | 257 | `DcDoubleParameter` v0 |
| Binding update state | 248 | 258 | `DynamicUpdateData` v1 |

Each dimension has a separate `Dimension` v1 continuation. Each capture binding has a separate `ManagedEntity` v1 continuation. Therefore each addition contributes six persistent physical records and four primary entities. Native export also replaces three existing plane-tracking cache/progenitor/recipe entities; those replacements are not additional dimension roles.

The primary dimension chain is `FusionSketchLinearDim v3 → SketchDimension v6`, stopping before `Dimension`. The continuation chain is `Dimension v1 → CommonBaseEntity v0 → ManagedEntity v1`. The binding primary chain is `DcDoubleParameter v0 → DcParameter v4 → DcData v0 → DcNode v2`, stopping before its `ManagedEntity v1` continuation.

### Exact class identities

| Class | Identifier | Version |
| --- | --- | ---: |
| FusionSketchLinearDim | `8C780195-72C0-4A56-A911-E43AB14357F2` | 3 |
| SketchDimension | `0C3F3829-F0DB-4379-9479-CFEF71087971` | 6 |
| Dimension | `855F0A64-6286-4FFC-B918-BC394F600107` | 1 |
| LinearDimensionInfo value | `735FD678-4ADD-4F4B-A8B1-88CAA010394E` | 3 |
| DimensionInfo value | `C2C193F2-E833-4842-8C93-A5B903F3A345` | 3 |
| Parameter | `7A6A3D31-BE74-4E19-9115-20642944C2E4` | 10 |
| DcDoubleParameter | `D91D429C-1BB5-4640-B49F-69AF14F463E9` | 0 |
| DcParameter | `B24D5130-8751-4272-8143-D230D8757873` | 4 |
| DcData | `D0D7E795-ECF7-48A8-A7A3-F983C5A29F8B` | 0 |
| DcNode | `A0A15D26-1F3B-4120-A3F1-9CDDA189AB74` | 2 |
| DynamicUpdateData | `6CCF41D5-40BE-48ED-A834-18F3EAED6C57` | 1 |
| CommonBaseEntity | `63D6AD42-466A-40B7-9CCD-EB21BC500EF6` | 0 |
| ManagedEntity | `CB844AB6-240D-4FC9-9C9F-3679DC896D6F` | 1 |

All versions above occur in the archive's metadata registry, including both nested dimension-info value classes. Exact spelling/case in records remains in the compressed evidence. Fields persist in lexicographic member-name order within each inheritance group, not registration order. The source declaration evidence records original C++ types, metatype identifiers and option masks. All listed dimension/binding/value fields have persistence mask 51.

## Complete dimension payload

The `FusionSketchLinearDim` own fields are `LinearDimensionInfo: Ns::Dimension::LinearDimensionInfo` followed by `RefPositions: vector<double>`. Both dimensions store `RefPositions=[0.0,1.0]`. The capture does not establish a general interpretation or allocation rule for those two values.

The `SketchDimension` own fields are:

| Field | Wire type | Width | Depth |
| --- | --- | --- | --- |
| constraintType | **uint64**, C++ `SKs::SketchConstraintType` | 4,194,304 (`1<<22`) | 8,388,608 (`1<<23`) |
| dcParameter | StrongRef to Entity | 247 | 257 |
| geometries | vector of PassiveRef to Geometry3D | A, B | D, A |
| isSick | bool | false | false |

The orientation correlation is established by the capture's explicit public API enum: horizontal for width, vertical for depth. It does not enumerate other `SketchConstraintType` flags. The referenced geometries are **point entities**, not the rectangle's lines. Width follows AB; the selected left edge follows DA, explaining the reversed geometric pair for depth.

The `Dimension` continuation stores `ParentNode: PassiveRef<Entity>=202`, opaque-display `color: four float32=(0,0,0,1)` and `isVisible=false`. `CommonBaseEntity.rClientObject` is null; `ManagedEntity.rParent` is the same sketch `202`. The primary frame has empty root ID, nonempty subjects and named uint64 metadata `EntityGenesis=0`; the continuation frame has only the empty root ID.

### Nested value field order and representation

`LinearDimensionInfo v3` owns, in wire order: `DimEndPoint`, `DimStartPoint`, `endPoint`, `extnStartPoint`, `isSingleArrow`, `length`, `startPoint`. Every point is three float64 centimetre coordinates, the Boolean is one byte, and `length` is float64 in centimetres.

Its base `DimensionInfo v3` owns: `bDriven`, `color`, `hasTextPoint`, `plane`, `prefix`, `text`, `textPosition`. Color is four float32 values. Plane stores a Boolean normal-reversal flag followed by origin, U axis and V axis, each three float64 values. Prefix/text are the ordinary wide-string wire values, and textPosition is another three-float64 point. There is no opaque annotation block.

The controlled values use `bDriven=false`, `hasTextPoint=true`, `isSingleArrow=false`, the XY plane, prefix `fx: `, and text equal to the referenced user parameter name. The annotation color is the float32 representation of approximately `(0.51,0.78,0.25,1)`. This display color is separate from the black `Dimension.color` field. The source chooses these display values; their general mandatory/default status is not established by one capture.

| Geometry before edits | Width | Depth |
| --- | --- | --- |
| startPoint / endPoint | (0,0,0) / (1.7,0,0) | (0,2.3,0) / (0,0,0) |
| DimStartPoint / DimEndPoint | (0,-0.5,0) / (1.7,-0.5,0) | (-0.5,2.3,0) / (-0.5,0,0) |
| extnStartPoint | (0,0,0) | (0,2.3,0) |
| textPosition | (0.85,-0.5,0) | (-0.5,1.15,0) |
| length | 1.7000000000000002 | 2.3000000000000003 |

## Parameter and binding graph

The two user parameters already exist in Baseline: `243 controlledWidth` and `244 controlledDepth`. They are `isUserDefined=true`, have no `dcParameter`, and remain children of parameter table `16`. The dimension addition does not create duplicate user parameters.

For width, dimension `245.dcParameter→247`, model parameter `246.dcParameter→247`, binding `247.parameter→246`, and binding `247.rrOwnerFeature→207`. Depth repeats the same joins with `255/256/257`. The binding's numeric value and model parameter's value equal the evaluated user parameter in centimetres. Only the model parameter expression names the user parameter; no new direct persistent reference to user parameter `243/244` is added to the binding.

`Parameter v10` persists all of the following ordered fields: `UserDefaultUnit:bool`, `actIdentifier:wide string`, `birthday:uint32`, `booleanValue:bool`, `comment:wide string`, `creationIndex:uint32`, `dcParameter:PassiveRef<Entity>`, `expression:wide string`, `expressionType:uint32`, `group:PassiveRef<ParameterGroup>`, `isDirty`, `isDriven`, `isExternal`, `isFavourite`, `isOrphan`, `isUserDefined` (Booleans), `name`, `textValue`, `unit`, `userName` (wide strings), and `value:float64`.

The model parameter qualified values are: empty actIdentifier/comment/textValue; birthday six; creationIndex three/four; false Boolean/status fields including `isDriven` and `isUserDefined`; expression `controlledWidth`/`controlledDepth`; expressionType zero; null group; name `Linear Dimension-2`/`Linear Dimension-3`; unit `mm`; userName `d3`/`d4`; and the evaluated centimetre value. These exact native names and birthday values are observations, not universal allocation constants. Base `rClientObject` is null and `rParent=16`.

`DcDoubleParameter.value` is float64. `DcParameter` persists `parameter:StrongRef<Parameter>`, `rparamId:uint64=1/2`, and `rrOwnerFeature:PassiveRef<DcFeature>=207`. `DcData` has no own saved members. `DcNode` stores `isActive=true`, `isEdited=false`, `isEliminated=false`, `rDynamicUpdateData→248/258`, null group representative and `rParentFeature=207`. Its separate ManagedEntity continuation has `rParent=27`, the Design node group. These two parents have different roles and cannot be collapsed.

`DynamicUpdateData` stores empty `bodies` and `predecessors` maps, false `isBodyOK/isPredecessorOK`, `rOwnerNode` back to the binding, uint64 timestamp and zero uint64 cross-reference predecessor hash. Native rebuild changes timestamps. Production authoring must supply its own coherent state policy, never copied timestamps.

## Membership, lookup and compute changes

For each addition, the following changes are observed together:

1. Add the dimension to `MSketch.dimensions` and the sketch's ManagedGroupEntity children. `MSketch.constraints` remains empty in all four captures.
2. Add the model parameter to ParameterTable children. Advance `highWaterMark` from 2→3→4, consistent with creation indices. Add the parameter name/ref to the helper's unordered parameterMap and a helper subject entry for that parameter at observer index zero. The saved map order is not lexicographic and is not a semantic evaluation order.
3. Add the binding to `DcSketch.dcParameters`, `DcFeature.childNodes`, and the Design node group's children. Advance `DcDesignFragment.nextParamId` from 0→1→2; this matches the latest allocated binding rparamId in this sequence.
4. Insert the binding before DcSketch in `DcComputeManager.sortedNodesAll`. After both additions, order is component33, plane-reference211, matrix215, widthBinding247, depthBinding257, sketch207. The manager remains current.
5. Add reciprocal dependency-manager entries: binding247→sketch207 with type one and binding257→sketch207 with type one. The sketch's existing component dependency type4096 and matrix dependency type1 remain. Both predecessor and successor maps are updated, and their current flag remains true.
6. Add binding timestamps to the sketch DynamicUpdateData predecessor map, while retaining existing component/sketch/matrix entries. The sketch's own update timestamp changes.

This captures graph construction requirements, not the general native scheduler algorithm. The point/line entities and CurveUses membership do not change when adding dimensions at their existing values.

## Observers are separate from dependency edges

The primary frame's subjects identify the observed entity and the observer's slot in that subject's observer vector. The exact dimension and binding subjects after both additions are:

| Observer entity | Observed subject → slot |
| --- | --- |
| Width dimension245 | AssetSettings0→4; A228→0; B230→0 |
| Depth dimension255 | AssetSettings0→5; A228→1; D234→0 |
| Width binding247 | DcSketch207→0 |
| Depth binding257 | DcSketch207→1 |
| Parameter helper17 | ParameterTable16→0; each parameter243/244/246/256→0 |

Subject order is not the same as `geometries`: the depth subject list is AssetSettings, A, D while its geometry pair is D, A. Geometry points do not gain persisted observer arrays; the reciprocal linkage is represented by these observer frames.

**Unresolved allocation boundary:** no persisted Baseline record in this Design segment observes AssetSettings0 at slots zero through three. Consequently the dimension's slots four/five cannot be reconstructed by counting only serialized Design observer frames. Native runtime observers, another segment or pre-existing transient subscriptions may explain them, but this analysis does not establish which. A new author must either obtain the constructor/loader contract or qualify an explicit supplied observer policy by native acceptance. Do not invent four entities or treat 4/5 as universal constants.

## Native edit results and limits

Changing the two user expressions to 19 mm and 29 mm updates both user values, both model parameter values and both DcDoubleParameter values. The model parameter expressions stay `controlledWidth`/`controlledDepth`. Dimension, binding and parameter entity identities and all subject joins remain unchanged.

The rebuilt corners are A=(0,-0.6000000000000005,0), B=(1.9000000000000001,-0.6000000000000005,0), C=(1.9000000000000001,2.3,0), D=(0,2.3,0), in centimetres. Thus the width is 19 mm and depth 29 mm, but the lower edge moves: the unanchored rectangle is not constrained to its original base. All four corner `isFixed/isFullyConstrained` flags remain false, and the geometric constraint list remains empty.

The four saved line-carrier start/displacement values change consistently with those points. Dimension annotation endpoints, textPosition and length update. Width `extnStartPoint` remains its original (0,0,0), even though width startPoint becomes (0,-0.6,0); retain the actual fields instead of assuming every annotation point equals the current reference point. Depth's upper reference remains fixed at y=2.3 in this solve. These observations do not establish a general deterministic anchor choice for every sketch.

Native solve/export also changes snapshot part IDs, MSketch.bodyId (0→2→4→7), tracking caches, revision UUIDs, dynamic timestamps and compute timing. Those are saved-state/cache effects, not dimension IDs, reference positions or constraint enums. The full delta retains them so they are not silently confused with required new dimension roles.

## Next independent-author contract

A qualified implementation can allocate fresh IDs for four logical dimension roles, produce both continuation chains, derive annotation geometry from declared endpoint/label inputs, bind a model parameter to a named user expression, and construct membership/compute/dependency edges explicitly. It must retain the uint64 constraint type, distinct user/model/binding identities, Point3D targets, parent roles and observer slots.

This evidence supports the exact horizontal/vertical point-to-point profile only. Before claiming independent editable width/depth authoring, the native application must accept a newly constructed graph, resolve both expressions, rebuild after changing each input, preserve one closed profile, save and reopen. Fixed placement, horizontal/vertical geometric constraints, other dimension types, driven/reference dimensions and integration with a subsequent extrusion require their own explicit scope and evidence.
