# Reflected Design Entity Graph Data Model

## Scope and evidence

This research codec decodes and reconstructs every indexed Design-segment record in three controlled Fusion 2706.1.17 documents: the circle sketch, its 7 mm extrusion, and its 13 mm extrusion. The result is 824 complete payloads, 75,675 payload bytes, and no unexplained payload tails. Encoding takes JSON-compatible typed values and exact schema declarations; it does not accept original payload bytes or residual byte arrays.

This is a qualified research result, not a complete Fusion format implementation. Other ZIP members and segments are outside this codec. BRep geometry is referenced by serializer entities but stored separately. The captured native schema describes the installed version, and most historical member sets are unavailable. Three custom recipe fields have proven widths and ordering but unresolved semantic names. Independent creation of arbitrary parametric graphs remains separate from reconstructing these controlled graphs.

The artifacts are:

- `GraphInventory.json.xz`: all 171 class declarations in the 7 mm extrusion, exact schema versions, inherited identifiers, member option masks, runtime type identifiers, and demangled C++ container types
- `GraphInventorySummary.json`: compact declaration, member-type, and unresolved-schema counts
- `EvidenceIndex.json`: compressed and uncompressed hashes and sizes for all three detailed evidence archives
- `GraphSummary.json`: three archive and stream hashes, record totals, and hashes of the complete compressed payload evidence
- `GraphPayloads.json.xz`: complete typed values and field offsets for all 824 payloads; the decompressed `GraphPayloads.json` is generated locally and ignored by Git
- `NativeComparison.json`: compact counts and every unmatched or unavailable comparison
- `NativeComparison.json.xz`: complete field-by-field comparison evidence
- `BodyMassCache.json`: body 261 cache/override schemas, payload offsets, captured values, and analytic cylinder comparisons

`Versions.json` has SHA-256 `54d93410a407ff808e5824c5ad797bf63fa89b3686e15be848960ca49ba4a161`. It is a native reflection capture, not a universal schema registry. Exact own-member sets are initialized for every declared class in these controlled graphs except the known empty `EntityMetaType` root. For inheritance, the codec resolves each class's own set using its own archive schema version; it does not trust the versionless base pointers embedded in another reflection lookup.

All execution described here was authorized research decoding and reencoding of saved captures. An earlier version also used static inspection of installed Fusion libraries. That material was removed. No local automated tests, production codec execution, or native Fusion execution were performed by this research subtask. Native load/edit acceptance was performed separately by the parent task and recorded in `../../LocalOracle/Features/CacheAcceptance.json`.

## Stable research interface

Load `DecodeGraph.py` with `runpy.run_path`. `read_graph(path)` returns:

- `archive`: independently parsed Design metadata, class declarations, and physical record information
- `codec`: the schema resolver and value codec
- `records`: physical-order entries containing `identity`, `primary`, `classCode`, `payloadBulkOffset`, and `value`

Each `value` contains a typed `frame` and ordered `groups`. Each group contains its literal class `identifier` and a dictionary of persisted `fields`.

`emit_record(codec, value, primary)` reconstructs one payload from that model. Its inputs contain no original payload. The caller rebuilds the enclosing bulk record headers and metadata indexes using an archive/segment writer. The research `archive` retains input bytes for inspection, but the encoder never reads them.

For body 261, find the primary record by `identity == 261`. Its current body group is `value['groups'][0]`. The cache is `fields['cache'][0]['fields']`; the four overrides are `fields['massProperties'][0]['fields']`.

The research interface reads reflection and class-name evidence from `re/`; it therefore must not be imported by production. `DecodeGraph.py` regenerates both compressed payload evidence and its compact summary. `CompareGraph.py` regenerates the native comparison archives. `InventoryGraph.py` regenerates the complete declaration inventory and compact summary.

## Record ownership and inheritance

The existing Design MetaStream indexes primary records and continuation records separately. Class declarations are local numeric codes with a literal identifier, base identifier, and schema version. A primary record's indexed owner determines its most-derived class. A continuation uses an ancestor class code and the same numeric entity identity.

The primary payload serializes its most-derived class's persisted members, then ancestor members, until an indexed continuation class is reached. The continuation starts at that ancestor and continues through subsequent ancestors until another continuation or the empty Entity root. Empty own-member sets still participate in the inheritance chain.

This distinction is essential. The 7 mm extrusion has 289 physical records, including 258 primary records and their continuation records. A `FusionComponent` record continues as `Component`; `MSketch` continues as `Sketch`; many feature entities continue as `ManagedEntity`. Treating every payload as all reflected inherited fields would double-read those ancestors.

The qualified declaration graph has 171 classes and 22 value classes. Class identifier text must be preserved literally and matched case-insensitively. Some identifiers are not valid UUID syntax. The actual `IntrinsicMetaTypeUuid` wire value is a separate concept.

## Entity framing

All integer widths below are little-endian. A narrow string is a `u32` byte count followed by that many bytes; the current research profile accepts ASCII. A wide string is a `u32` count of UTF-16 code units followed by UTF-16LE data.

| Payload kind | Fields before schema members |
| --- | --- |
| Primary | narrow `rootId`; strict `bool hasEntitySubjects`; optional subjects; strict `bool hasNameValuePair`; optional named metadata |
| Continuation | narrow `rootId` only |

If `hasEntitySubjects` is true, a `u32` subject count follows. Each subject consists of a passive reference and an `i32 indexInObserverVec`. This index belongs to the subject/observer relationship. It is not a parameter creation ordinal or an arbitrary owner-control word.

If `hasNameValuePair` is true, a `u32` entry count follows. Each entry is a narrow name, a narrow member-metatype identifier, and that type's value. The controls contain `EntityGenesis`, `pt_tag`, `crv_primary_id`, `crv_secondary_id`, and `crv_tag_id_idx`, all using `IntrinsicMetaTypeuint64`. Their complete offsets are in the compressed payload evidence. Other named value types are not qualified by these captures.

A nonempty primary `rootId` identifies a named root entity. On disk it still has the numeric identity used by ordinary references. Native `PEntity.Properties` reports such a target as `entityId = -1` with its `rootId` string. This difference is normalized through the primary record's root name during semantic comparison; it is not evidence of an inline string-reference wire variant.

## References

The controlled same-asset reference layout is:

1. Strict `bool notNull`; false terminates the reference
2. `u64 entityId`
3. Strict `bool crossAsset`; the current codec rejects true
4. Strict `bool differentSegment`
5. If `differentSegment`, a `u32 segmentId`

A local numeric reference is therefore 11 bytes. A same-asset cross-segment reference is 15 bytes. The two bytes after the identity in a local reference are meaningful false flags, not reserved padding. The controlled captures hold both the local and the cross-segment form. The names of the two flags came from removed static evidence and are not confirmed by a black-box experiment.

The controlled Design segment references the ACT segment. Archive segment identifiers and runtime-loaded segment identifiers differ; comparison shifts by the captured Design segment offset. This normalization is validated only for these controlled imports and must not become a universal assumption for arbitrary native sessions.

Cross-asset and cross-document references have additional link, document, asset, and metatype information. They are rejected here. Root references, cross-segment references, unresolved references, and cross-document links must remain distinct types in a future general model.

## Primitive and collection values

| Native metatype | Wire encoding |
| --- | --- |
| `IntrinsicMetaTypebool` | `u8`, strictly 0 or 1 |
| `IntrinsicMetaTypeuint8/uint16/uint32/uint64` | unsigned integer of the named width |
| `IntrinsicMetaTypeint32` | signed 32-bit integer |
| `IntrinsicMetaTypefloat` | IEEE-754 binary32 |
| `IntrinsicMetaTypedouble` | IEEE-754 binary64 |
| `IntrinsicMetaTypeIString` | length-prefixed UTF-16LE |
| `IntrinsicMetaTypeHString` | length-prefixed narrow text |
| `IntrinsicMetaTypeUuid` | length-prefixed UTF-16 UUID text, not 16 raw bytes |
| `StrongRefMetaType`, `PassiveRefMetaType` | reference framing above |
| `Vector`, `List`, `Set` | `u32` count, then element values |
| `Map`, `HashMap` | `u32` count, then key/value pairs |
| `std::pair<A,B>` | A followed by B, with no count or pair header |
| `PrivatePointer<T>` | `u32` count restricted to 0 or 1, followed by T when present |

The member metatype name `Vector` or `Map` does not supply element types. The demangled `debug_type_name` does. Nested templates preserve distinctions such as a list of pairs of a list of sketch tags and a boolean. Treating all collections as references would silently corrupt manager maps, parameter registries, recipe values, and byte vectors.

Hash maps preserve their serialized iteration sequence in the typed model so exact reconstruction remains possible. Native semantic comparison ignores hash-map entry order; the on-disk order is not the same as the native JSON iterator order. Set and map elements must be represented as typed values, not a binary cache.

The dependency-manager enum `Na::DesignCapture::EDcDependencyType` occupies a four-byte unsigned slot in the observed nested maps. Values 1, 4, and 4096 agree with the native graph. The current research implementation names that enum explicitly; promotion should derive and retain enum widths in its declarative type descriptors rather than assume every C++ enum is four bytes.

An empty collection proves only its count framing. Nonempty values of otherwise unsupported element types must be rejected until their layouts are independently qualified.

## Reflected values and callback overrides

For ordinary registered value classes, members are serialized in lexical name order, followed by base value members. There is no additional value-object framing in these controls. Native class versions are supplied by the Design metadata, including declarations for value classes.

A member is persisted when `option_mask & 1` is nonzero. The default mask is `0x33`. Transient field declarations remain part of the schema but contribute no bytes to this ordinary-save profile. For example, feature cache history fields and `ManagedEntity.expanded` are excluded. Undo, clone, and copied-asset masks have separate semantics and are outside this save profile.

Reflection alone cannot prove member order or complete payload structure. A value can have reflected members and also install a custom save callback. `ColorValueMetaType` is the decisive example: alphabetical member decoding reconstructed every original byte but mislabeled red as alpha. The native semantic comparison exposed the error. It supports red, green, blue, alpha as four floats.

An earlier static audit listed which of the 22 declared value classes install custom save callbacks. That audit was removed. Its list is not confirmed by a black-box experiment. In these controls, color, the geometry types, sketch tag, and profile edge tag need a class-specific layout. The other value classes agree with ordinary lexical persistence in the byte-identical reconstruction and the native semantic comparison.

| Value class | Qualified layout |
| --- | --- |
| `Color` | red, green, blue, alpha as four f32 values |
| `AcGePoint2d` | x, y as f64 |
| `AcGePoint3d`, `AcGeVector3d` | x, y, z as f64 |
| `AcGeMatrix3d` | identity bool; if false, 16 f64 values in row/object order |
| `AcGeLine3d` | point on line, then `evalPoint(1) - pointOnLine`, each three f64 values |
| `AcGePlane` | normal-reversed bool, origin, u axis, v axis; each point/vector is three f64 values |
| `AcGeCircArc3d` | center, normal, reference vector, radius, start angle, end angle |
| `BBox` | lexical max then min, each point3d |
| `GlobalizedString` | lexical reflected fields: defaultValue, globalized, id, moduleName, value |
| `MassProperties`, `MassPropertyCache` | lexical reflected members, detailed below |
| Physical/visual material | lexical reflected fields, including nested color and asset-manager reference |
| Occurrence/base occurrence/ACT passive path | lexical own members and base value members; collections and references retain their typed schemas |
| Passive scope | asset UUID, scope entity identifier, scope-id type, segment id in lexical order |
| Feature tag info | lexical face primitive byte vector, offset vector, operation id, primary flag |
| Sketch-region recipe data | lexical faceRecipe then originalFaceRecipes; nested lists/pairs/sketch tags |

Byte-identical reconstruction and the native JSON comparison support these layouts for the controlled captures. The plane representation preserves its parameter axes; the native JSON projection exposes only a point and normal. Identity matrices occur in the controlled captures. The nonidentity matrix branch and the line direction reading came from removed static evidence. They are not confirmed by a black-box experiment. A new native nonidentity control is still required before claiming target-application acceptance for that branch.

## Sketch tag and profile recipe values

`sketch_tag_idValueMetaType` has schema version 2 in the metadata. Its current callback writes an internal tag `version` value of 3 in these captures. These two versions are different layers.

The 40-byte current sketch tag is:

| Offset | Field | Type |
| --- | --- | --- |
| 0 | version | i32 |
| 4 | tagId | u64 |
| 12 | secondaryTagId | u64 |
| 20 | direction | u32 boolean, normalized to 0/1 |
| 24 | splitSequenceId | u32 |
| 28 | splitTotalNumber | u32 |
| 32 | objectOffset20 | u64; semantic name unresolved |

The runtime reflection capture names `tagId` and `direction`. The other names came from removed static evidence and are not confirmed by a black-box experiment.

The profile-edge tag value has an internal i32 version, a counted vector of sketch tags, and two counted ordered sets of u64 values. Their semantic names remain unresolved. The controlled profile has version 0, one sketch tag with tagId 102, and both sets empty.

These three unresolved semantic fields are represented as typed integers/sets with explicit offset labels. They are not opaque byte spans, but they also must not be presented as a complete semantic data model. Native `PEntity.Properties` omits these callback internals: a nonempty sketch tag appears as an empty JSON value. Byte-identical reconstruction of the controlled payloads supports the widths and order.

## Body mass cache

Body 261's primary payload is 879 bytes. The `cache` field starts at payload offset 24 and uses `MassPropertyCacheValueMetaType` version 0.

| Payload offset | Field | Type |
| --- | --- | --- |
| 24 | area | f64 |
| 32 | areaPrec | f64 |
| 40 | cog | three f64 |
| 64 | inertiaPrec | f64 |
| 72 | moi | three f64 |
| 96 | moiOffDiag | three f64 |
| 120 | revisionGuid | UTF-16 UUID text, 76 bytes in these captures |
| 196 | volume | f64 |
| 204 | volumePrec | f64 |

`MassPropertiesValueMetaType` version 0 follows elsewhere in the body fields: areaOverride at 227, densityOverride at 235, massOverride at 243, and volumeOverride at 251, each f64. All four are -1 in the controlled captures.

Native JSON agrees with every cache and override field, subject to its decimal rendering precision. With radius 1 cm and height h, the observed moments agree with geometric moments about the global origin: `Ixx = Iyy = volume * (r²/4 + h²/3)` and `Izz = volume * r²/2`. They do not use the centroid formula. The stored integration results differ slightly from exact analytic cylinder values.

The revision GUID changes between the two native saves, but its invalidation contract is not inferred from that observation. The three precision fields are retained as native data; inventing confidence values is outside the proven model. The parent native replacement experiment retained original caches and independently observed fresh geometry-derived mass properties on initial load, so a cache rewrite was not necessary for that acceptance path.

## Semantic comparisons and limits

After accounting for script-property aliases, named-root identity presentation, archive/runtime segment ids, hash-map order, and native float rendering, the saved native graphs match 1,280 circle fields, 1,585 7 mm fields, and 1,588 13 mm fields.

The remaining comparisons are explicit:

- Each saved component's userName is `(Unsaved)` while its live property snapshot reports `Untitled`
- Three empty texture-mapping bounding boxes in the 7 mm archive contain finite +/-DBL_MAX sentinels, while the captured native JSON contains infinities
- Two recipe properties in each extrusion cannot expose their callback internals through the captured native JSON

Named roots without positive native numeric IDs were unavailable in the original graph capture. Their payloads still reconstruct exactly, but lack that independent property comparison. The complete comparison artifact records these missing entities.

Byte-identical reconstruction establishes syntactic completeness for these payloads. Native property agreement strengthens semantic field attribution. Native load/rebuild/edit acceptance establishes another boundary. None of these, alone, proves an independently authored full archive or complete historical/corpus support.

## Smallest additional native controls

1. A sketch on a translated and rotated construction plane, with a nonzero circle center and partial arc, qualifies nonidentity matrix ordering, noncanonical plane axes, and nontrivial curve values together
2. A circle split by another curve, followed by a profile extrusion, varies splitSequenceId and splitTotalNumber and supplies multiple sketch tags
3. A projected/intersected or derived sketch profile can vary secondaryTagId and the unresolved tag extension; capture both payloads and any native debug/string recipe representation available
4. A profile whose progenitor includes nonempty operation-id sets is needed to name the two profile-edge sets; empty-set fixtures cannot establish their semantics

No extra control is needed merely to repeat the proven 7 mm/13 mm payload reconstruction. Cross-asset references and historical schema migration require their own controlled documents and remain out of this profile.

## Production promotion partition

Production must not load the runtime reflection captures, binary maps, installed CAD libraries, or research scripts. A promotion can be partitioned into:

1. **Schema catalog and lineage:** immutable typed declarations for the qualified 171 classes and exact versions, including persistence flags, reference types, nested collection descriptors, base identifiers, and callback selection. Resolve every inherited and nested version against archive metadata and reject unsupported versions
2. **Value model and primitives:** explicit finite/range-validated scalar, string, UUID-text, reference, point/vector/matrix, color, sequence, pair, and map records. Separate original container iteration order from semantic equality. Keep callback-backed values distinct from ordinary reflected structs
3. **Entity framing:** named-root id, subjects with signed observer indexes, supported typed name/value entries, primary/continuation ownership, and exact member-group boundaries
4. **Qualified entity codec:** all current controlled graph classes, typed decode and emit with no original payload input. Reject unknown types, nonempty unsupported collections, cross-asset refs, extra fields, trailing bytes, illegal counts, duplicate keys where forbidden, and unqualified callback branches
5. **Archive assembly integration:** rebuild class ownership, primary/continuation indexes, physical record lengths, and archive member tables from semantic records; connect independently authored serializer/BRep content through explicit ids

The unresolved recipe semantic fields should remain research-only until their contracts are recovered or the product exposes a narrowly qualified, explicitly typed current-profile representation without pretending to support arbitrary authoring. Existing feature and parameter production codecs should share the same validated primitives and schema descriptors rather than acquire a second divergent implementation. Whole-archive CI integration must cover typed reconstruction, meaningful semantic edits, unsupported inherited versions, unsupported callback branches, and native acceptance. No local test execution is required to promote the code.
