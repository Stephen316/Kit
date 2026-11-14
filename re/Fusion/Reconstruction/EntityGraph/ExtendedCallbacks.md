# Complete corpus Design record framing

The read-only [corpus inventory](../CorpusSemantics/Summary.json) now decodes all **261,141 indexed Design records in 712 archives**, consuming **25,458,293 of 25,458,293 payload bytes**.
There are no archive failures or unexplained record suffixes.
The compressed inventory retains source digests, class/version, record identity, payload offset, consumed length, and field count for every record.
This is structural and typed-field coverage.
It is not a claim that all 712 designs have independently regenerated geometry or vendor acceptance.

The initial inventory decoded 256,522 records.
The remaining 4,619 were ordinary named metadata, three geometry value callbacks, ASM persistent selection recipes, and one lazily initialized auxiliary value.
`InitialSummary.json` and `InitialInventory.json.xz` preserve that earlier measurement.
The callbacks below close the gap.
They do not replace the separate BRep journal and topology codecs.

## Evidence and method

The evidence is the complete corpus decode above.
It supports the byte framing below: every field width and count consumes the payloads exactly.
It does not by itself confirm field names or meanings.

An earlier version also cited function excerpts from installed Fusion libraries.
That material was removed.
Field names and meanings below came from it unless the text names corpus or black-box evidence.
They are not confirmed by a black-box experiment.

Research implementations are [CurveValues.py](CurveValues.py), [RecipeValues.py](RecipeValues.py), and [ProgenitorValues.py](ProgenitorValues.py), dispatched by [DecodeGraph.py](DecodeGraph.py).
They serialize from named values and receive no retained field payloads.

## Common encodings

All numbers in these callback payloads are little-endian.
`i32`, `u32`, `u64`, and `f64` have their normal fixed widths.
A boolean is one byte, restricted to zero or one.
A point or vector is three `f64` coordinates.
A recipe collection has an `i32` nonnegative count; the research reader bounds it to one million elements.
Recursive recipe payloads are limited to depth 64.
Type names are an `i32` byte length followed by ASCII with no terminator.

These callback collections differ from the enclosing entity model's generic collection contracts.
A reader must dispatch according to the declared metatype.
It cannot infer a single universal container layout from a leading integer.

## AcGe geometry callbacks

Runtime reflection does not describe the serialized members of these callbacks.
The three additional callbacks frame as:

| Metatype | Persisted fields in order |
| --- | --- |
| `AcGeLineSeg3dValueMetaType` | `startPoint: xyz`, `displacement: xyz` |
| `AcGeEllipArc3dValueMetaType` | `center: xyz`, `majorAxis: xyz`, `minorAxis: xyz`, `majorRadius: f64`, `minorRadius: f64`, `startAngle: f64`, `endAngle: f64` |
| `AcGeNurbCurve3dValueMetaType` | `evalMode: bool`, `isPeriodic: bool`, `degree: i32`, knot vector, weight array, control-point array, interval |

Kit reads the second line-segment vector as end minus start, not the end point.
That reading came from the removed static evidence.
It is not confirmed by a black-box experiment.

The knot vector is `tolerance: f64` followed by a geometry array of doubles.
Each geometry array is:

1. `logicalLength: u32`.
2. `physicalLength: u32`.
3. `growLength: u32`.
4. Exactly `logicalLength` elements.

The corpus frames with exactly `logicalLength` elements, so the file holds no inactive capacity values.
Kit treats `physicalLength` and `growLength` as allocation descriptors.
That meaning is not confirmed by a black-box experiment.
The point array uses XYZ elements; knot and weight arrays use doubles.
Logical length must not exceed physical length.

The NURBS callback carries no separate rationality byte in the corpus framing.
Weights convey the rational representation.
Inventing a rationality byte would shift every following field.
The interval is `tolerance: f64`, `boundedBelow: bool`, `boundedAbove: bool`, `lowerBound: f64`, `upperBound: f64`.
The observed corpus profile includes the interval.
Whether older geometry-library layouts omit it is not confirmed by a black-box experiment.

### Matrix callback

The matrix callback writes a boolean identity marker.
True ends the value.
False is followed by exactly sixteen doubles.
There is no extra row count or affine-only truncation.
This layout came from the removed static evidence and is not confirmed by a black-box experiment.
The independent author uses identity matrices.
Broader readers must explicitly qualify and retain all sixteen nonidentity coefficients.

## ASM persistent selection recipes

The GUID `B28C1CCE-7FBD-43D2-8313-02BEC60F73FD` identifies `SMI_TAGGING_TRACKING::RECIPEValueMetaType`.
This value records persistent selection and tag relationships.
It is not the body's BRep topology or the `.smbh` modeling journal.

The recipe value frames as:

1. `version: i32`.
2. `tags: counted<tag_info>`.
3. `lwdTags: counted<tag_info>`.
4. `payloadType: counted ASCII`.
5. The payload selected by that exact type name.

All **1,763** top-level recipe values in the corpus use version **3**:

| Payload type | Corpus values |
| --- | ---: |
| `body_recipe_data` | 289 |
| `bounded_face_recipe_data` | 171 |
| `edge_recipe_data` | 844 |
| `face_recipe_data` | 243 |
| `vertex_recipe_data` | 216 |

`base_recipe_data` does not occur as a top-level value in this inventory.
Nested face, edge, and vertex payloads carry no repeated type-name string because the containing vector fixes their type.

### Tag tables

A `tag_info` is a counted vector of `tag_data`.
Each `tag_data` contains:

| Field | Wire type |
| --- | --- |
| `primaryId` | `i32` length, then bytes |
| `secondaryId` | `i32` |
| `operationIds` | `i32` count, then `i32[]` |
| `approachId` | `i32` |

The primary identifier is a typed variable-length identifier.
It is not an unparsed recipe payload.
It need not be treated as a null-terminated string.
The implemented research profile admits version 3 only.
Older layouts are not observed and not qualified.

### Payload inheritance and topology context

Every payload starts with one `i32` that this model calls `primaryTagIndex`.

| Payload type | Fields after `primaryTagIndex: i32` |
| --- | --- |
| `body_recipe_data` | `lwdTagIndex: i32` |
| `face_recipe_data` | `lwdTagIndex: i32` |
| `bounded_face_recipe_data` | `lwdTagIndex: i32`, counted edge payloads |
| `edge_recipe_data` | `lwdTagIndex: i32`, counted face payloads, counted vertex payloads, `referenceFaceIndex: i32` |
| `vertex_recipe_data` | counted face payloads, counted edge payloads, ordered UV map |

The acronym `lwd` is retained without inventing an expansion.
Edge and vertex nesting is finite on disk but recursive in the type model.

### UV order map

The vertex payload's map is `count: i32`, followed by entries of `key: i32` and seven `i32` values.
The key's exact semantic role is not asserted.
Kit names the seven values:

1. `faceVertexCount`.
2. `uOrder`.
3. `uLowerOrder`.
4. `uUpperOrder`.
5. `vOrder`.
6. `vLowerOrder`.
7. `vUpperOrder`.

These names came from the removed static evidence.
They are not confirmed by a black-box experiment.

## Lazily initialized progenitor metadata

The GUID `BE7E2847-FBC4-4898-A6E7-632A559A7F89` identifies `ProgenitorAuxDataValueMetaType`.
The runtime reflection capture listed its version-zero member set as uninitialized.
That state is not evidence that the value is empty.

The value is four bytes in every corpus record; see [ProgenitorValues.md](ProgenitorValues.md).
All 38 previously unresolved named metadata values now decode: 36 in `SweepFaceProgenitor` records and two in `EntityProgenitor` records.

## Acceptance boundaries

This inventory consumes every indexed Design record in the supplied corpus.
It does not prove semantic correctness of every feature algorithm.
It does not regenerate arbitrary NURBS BRep bodies, interpret every auxiliary package, or vendor-load every rewritten archive.
The independent parameter, circle, and extrusion documents have separate native load/edit/rebuild/rollback/save/reopen evidence in [DocumentAuthoring/Acceptance.md](../DocumentAuthoring/Acceptance.md).

The interpretation also retains explicitly named uncertainty in earlier sketch/profile callbacks and in the UV map key.
Knowing every byte's type and boundary is stronger than preserving residual payloads.
It is weaker than knowing every algorithm that uses those values.
Production support must state its qualified schema and geometry profile, reject unsupported cases, and carry its own acceptance evidence.
