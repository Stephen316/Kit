# cadmpeg F3D knowledge compared with Kit's Fusion model

- Upstream: cadmpeg, <https://github.com/cadmpeg/cadmpeg>, commit `de2726870ff728352163f601ab4e60bbd54fbade`, read from the untracked local checkout `re/Fusion/External/cadmpeg`.
- License: cadmpeg code is Apache-2.0 (`LICENSE`); its specifications are CC-BY-4.0 (`LICENSE-docs`, `docs/formats/f3d.md:3`) with attribution to the cadmpeg project. Kit does not copy cadmpeg code and does not vendor it. This file is a cited comparison only; short quoted phrases are attributed to cadmpeg.
- Date: 2026-11-12.

## Scope, method and citation keys

The comparison read cadmpeg's F3D specification, its open items, the Fusion section of its support ladder, the ASM specification and open items it delegates to, and the F3D writer sources. On the Kit side it read the data model, the BRep wire model, the acceptance matrix and the Kit documents those three link for the specific topics below. A read-only script resolved cadmpeg-cited class GUIDs against Kit's class catalogue. No tests, builds, `cargo` or `pytest` were run. A correspondence derived only from byte-offset arithmetic, or from absence in a text search, is marked **inferred** or **unverified**.

| Key | Path (cadmpeg paths are under `re/Fusion/External/cadmpeg/`) |
| --- | --- |
| F / FO | `docs/formats/f3d.md` / `docs/formats/f3d-open-items.md` |
| A / AO | `docs/formats/asm.md` / `docs/formats/asm-open-items.md` |
| S | `docs/format-support.md` |
| W | `crates/cadmpeg-codec-f3d/src/writer/` |
| DM | `Documentation/Reference/Research/FusionDataModel.md` |
| BR | `re/Fusion/Reconstruction/BrepDataModel.md` |
| AE | `Documentation/Reference/Research/FusionAcceptanceEvidence.md` |
| TS | `re/Fusion/Reconstruction/TSpline/FieldModel.md` |
| GT | `Documentation/Changes/Fusion/FusionGenericTagSemantics.md` |
| HS | `Documentation/Changes/Fusion/FusionHistoryStates.md` |
| HM | `re/Fusion/Reconstruction/HeaderGrammar/HeaderModel.md` |
| BC | `re/Fusion/Reconstruction/BinaryClasses.json` (1,218 GUID-to-class mappings for Fusion 2706.1.17; every identifier also appears in runtime reflection) |

Line numbers are pinned to the cadmpeg commit and to this Kit working tree. Kit already credits cadmpeg at DM:31-34, DM:77-80, DM:526-528, BR:13, BR:55, BR:104, BR:136 and TS:11.

## Summary

- The two projects describe the same container bytes. Most container differences are vocabulary: cadmpeg describes frames positionally, and Kit names fields from runtime reflection and saved documents. Some Kit names came from earlier binary inspection, which was removed; those names are research labels.
- cadmpeg is much broader: about 58 feature families, assemblies and cross-document references, configurations, T-spline Form graphs, ParaMesh attribute channels, and a large ASM procedural and tolerant-geometry vocabulary. It records 198 F3D and 43 ASM open items.
- Kit is narrower and deeper on what it covers. It names native members and allocators, and it independently authors complete parametric documents that Fusion 2706.1.17 opens, rolls back, rebuilds, edits, saves and reopens.
- cadmpeg's writer replays or patches retained source archives. Its source-less generator writes B-rep, ASM history, selected Design records, configurations and appearances. It does not write ACT, Browser, feature scopes, owned parameters or sketch placements. No record of Fusion opening cadmpeg output was found.
- Kit's black-box evidence contradicts several cadmpeg statements: TSM link order, the crease namespace, the equal `history_stream` preamble fields, the generic-tag "selector" and vertex `index_flag`. Kit's earlier binary inspection also disagreed on `ec`, namespace 50000 and the history-flag rule; those points are not confirmed by a black-box experiment. Kit answers two cadmpeg open items in part (HS-01, DR-80) and gives names or inferred answers for several more (§5.2).

## 1. Container and segment layer

| Topic | cadmpeg | Kit | Assessment |
| --- | --- | --- | --- |
| ZIP | Stored, DEFLATE or zstd method 93 (F:11) | Corpus has stored and Zstandard members; method 93 breaks older tools (DM:9-10, DM:53) | Agree |
| Segment pairs | `MetaStream.dat` + `BulkStream.dat` for Design, ACT, Browser (F:20-23) | Same three kinds (DM:89-91, DM:180-182) | Agree |
| MetaStream header | Short type name, u32 segment ID, LP-UTF16 "asset GUID", u32 magic, three u32 when magic is 1234, full type name, add-in name, two u32 whose first is type code 1/5/6 (F:468, F:486) | Kind, ID, segment `currentVersion` UUID, magic 1234, metadata version 8, one u64 packed software version, type identifier, add-in, `neutronType`, ancestry-UUID count (HM:3-9) | Same bytes. Kit names the four words that cadmpeg leaves positional. The two disagree on the UUID's meaning. |
| Names and IDs | The two type names can differ; segment IDs are not fixed (F:468, F:486) | Kit's check requires equal names and ACT=1, Browser=2 (`src/convert/formats/Fusion/MetaIndex.py:15-19`, `:33-38`) | Kit's admitted profile is narrower |
| Type table | Type GUID, base GUID, u32 version, add-in, counted u64 IDs; 36- or 37-character opaque GUID strings (F:470-474) | `MetaClass` with the same fields (DM:172) | Agree |
| Named-entity list | Exactly the IDs whose record has a nonempty name (F:476, F:484) | `StoredIds` retained without a meaning (DM:174) | cadmpeg gives a testable meaning |
| Indexes | Primary and secondary; a secondary offset lies inside its primary record and starts a nested header that bounds one class level (F:476, F:484, F:523) | Primary and continuation; a continuation selects an ancestor class and the indexer verifies ancestry (DM:175-176, DM:207-210, DM:595) | Same mechanism, different words |
| After the next-ID counter | u32 version-context count, then contexts (u64 token, GUIDs, version URN, revision); a segment can end earlier (F:476-480) | `Reserved` u32, then properties (DM:177; `SegmentCodec/Metadata/ReadMetaWire.py:31-32`) | Gap in Kit |
| Property block | `(LP-ASCII key, u32)` pairs (F:482) | Persisted per-module migrator numbers (DM:178, HM:17) | Agree; Kit gives the meaning |
| Record header | "LP-ASCII decimal class tag, the u64 entity ID, and an LP-ASCII record name" (F:525); elsewhere an 11-byte header with a u32 `record_index` (F:653), explained as a 32-bit reading of the u64 (F:513) | u32-counted ASCII code, u64 identity, counted root-identity string (DM:187-194) | Same bytes. cadmpeg uses both a u64 reading and a u32-plus-zeros reading. |
| Class code | 256 plus type-table row; local to the segment (F:525) | Same (DM:130, DM:207) | Agree |
| Payload prologue | Presence byte for a "class-defined leading block", then a property-block flag with `(key, type, value)` triples (F:519-521) | Entity-subjects flag and rows `(passive reference, i32 indexInObserverVec)`, then a named-metadata flag (DM:192-201) | Same framing, different meaning (§1.1) |
| Member order | Most-derived level first, case-sensitive lexical order (F:517) | Lexical order per member set; option-mask bit `0x1` drops a member; custom callbacks override (DM:203-205, DM:572-576, DM:673) | Agree; Kit adds the exceptions |
| References | Full grammar: null (1 B), local (11 B), cross-segment (15 B), cross-document with asset GUID, link name and optional version URN, inline-typed (51 B) (F:488-515) | Local `01 u64 00 00` (DM:155). The reader accepts cross-segment and rejects cross-asset references; it has no inline-type branch (`src/convert/formats/Fusion/EntityCodec/Wire/ReadRefMut.py:8-16`) | Gap in Kit. Whether Kit's corpus contains the inline-typed generation is unverified. |
| Manifests | Top-level and per-asset grammar, legacy generation header, capability registry, terminal forms such as `NA_EXPORT` and `NA_OFFLINESAVE` (F:238-281) | Controlled manifests fully decoded; document `identifier`/`currentVersion`; the value 5 is the next segment ID (HM:17-19; `re/Fusion/Reconstruction/DocumentEnvelope/EnvelopeRecipe.md:53-63`) | Overlap. cadmpeg covers more variants; Kit names the allocation fields. |
| F3Z | `Manifest.json`, `DesignDescription.json`, F2D-root variant (F:405-421) | Bundle codec with nine-document cloud acceptance (DM:655, AE:32) | Agree |

### 1.1 The leading block and cadmpeg "role" codes

cadmpeg treats the block after the record name as class-specific, for example "a sketch relation's pair list" (F:519). It reads the u32 after each reference as a semantic code: `local_ordinal` in parameter owners (F:663), and "role" in dimension frames (F:727, F:733, F:737). Kit identifies one generic `Ns::EntityMetaType` subjects list in this position. The integer in each row is the subject's `indexInObserverVec`, which is "not a feature-control position" (DM:198-201). Kit also states that observer slots are allocated independently for each target entity (DM:766).

**Hypothesis (unverified).** The rows have the same shape, so cadmpeg's role codes may be observer-vector positions, not geometric roles. If so, F:729's "both role codes nonzero" rule would depend on allocation history. Kit can test this on its own constrained-rectangle archives.

## 2. Parametric layer

### 2.1 Numeric parameter fields

cadmpeg describes the record by layout forms (F:655-657). Kit describes it by native lexical members (DM:284-347).

| cadmpeg term | Kit native member | Note |
| --- | --- | --- |
| `source_ordinal` | `creationIndex` | Kit: allocation index; deletion leaves gaps (DM:132, DM:253-261) |
| Wide-form "family discriminator", u32 at offset 26, values 0-6 | `birthday` = expression-engine `latestVersion`, observed 6; "it is not a date" (DM:325, DM:345) | **Inferred**: 11-byte header + 15 zeros equals Kit's 15-byte header + root count + 7 bytes |
| Owner: `u8 1 + u32 owner_record_index` or null | `dcParameter` passive reference to the binding (DM:289, DM:329) | cadmpeg's "owner" is Kit's binding record |
| 11-byte wide trailer: text flag, zeros, driven, zero, favorite, zero, document flag | `expressionType`, `group`, `isDirty`, `isDriven`, `isExternal`, `isFavourite`, `isOrphan`, `isUserDefined` (DM:311, DM:331-338) | **Inferred** one-to-one; document flag = `isUserDefined` |
| `source_kind`, unit token, name, scalar | `name` (role), `unit`, `userName`, `value` | Agree; both store cm and radians (F:655, DM:396-398) |
| 12-byte tail `u8 0` + collection reference | Inherited null `rClientObject` + `ManagedEntity.rParent` (DM:346-347) | Same bytes; Kit names both |

### 2.2 Binding, companion, collection and timeline

The cadmpeg owner frame (F:663) has the same layout as Kit's `DcDoubleParameter` binding (DM:357-377):

- `01 + u32 1` is the subject list.
- `local_ordinal` is `ObserverIndex`.
- `00 + f64` is the metadata flag and `Number`.
- `owned_ordinal` plus four zero bytes is the u64 `RuntimeParamId` (`rparamId`).
- The trailing `01 variant flag` is Kit's fixed `01 00 00`. Neither project explains it (FO:422 DR-87).
- The companion reference is Kit's `BookId`.

The companion is `Na::DesignCapture::DynamicUpdateData` (BC; DM:384-386). cadmpeg says its timestamp is a Unix-epoch wall clock in microseconds, preserved across saves (F:677). Kit establishes microseconds only for macOS libc++, leaves the epoch and portability unproven, and forbids invented defaults (DM:387-392). The collection is covered in §5.2.

The timeline record is `DcCreationOrderFeatures` (BC). cadmpeg's grammar has a context reference, ordered item references, optional trailing nulls and several timelines per stream (F:527-529). This matches Kit's history payload (DM:220-227).

### 2.3 Features, sketches and depth

cadmpeg defines a feature scope as primary and paired headers with the same index, a localized family name, a family-local ordinal and two ASM history-state identities. These identities join the scope to `delta_state` IDs (F:464, F:765). Its table has 58 family GUIDs (F:771-830). The script resolved all 58 in BC to `Dc*` classes that match the labels, for example `Extrude` to `DcExtrudeFeature` and `Component Insert` to `DcXRefPCIFeature`. Kit has reflected schemas for 401 of 403 corpus classes (DM:539) and full own-field lists for the sketch and extrusion classes (DM:607-651). **Inferred:** the two state identities correspond to the persisted `startModelHS`/`endModelHS` (DM:575).

The two projects use different methods for sketches:

| Topic | cadmpeg | Kit |
| --- | --- | --- |
| Profiles | Loops are computed from curve endpoint incidence and planar arrangement (F:639-645) | A profile is an explicit selection of bounded curve portions (DM:407) |
| Dimension targets | A dimension governs geometry whose measured value equals the parameter, within tolerance (F:687, F:701, F:733) | Dimensions are explicit records with their own parameters and observers; they "cannot be modeled as coordinates" (DM:722, DM:766) |
| Constraints | Coincident, midpoint, symmetry, offset, distance, angle, radius and pattern relations transfer (S:360) | Horizontal/vertical constraints, fixed points and linear dimensions for rectangles (DM:750, DM:766) |
| Point records | Versions 0/8/10/11, flags, `EntityGenesis`, `CurveUses` companions (F:583-607) | Sketch split ordinals and attribute semantics (DM:659, DM:667) |

**Depth.** cadmpeg decodes parameter expressions, evaluated values, dependency identities, and feature operands for the families it projects into a neutral IR. It does not regenerate geometry: "the Fusion feature history is not yet replayable" (S:360), and L6 is blocked (S:348). Kit also has no solver. It authors analytic solved caches for qualified profiles and uses Fusion's rebuild as the acceptance oracle (DM:702, DM:734-738).

### 2.4 cadmpeg labels and Kit's native class names

| GUID prefix | cadmpeg label | Kit catalogue class (BC) |
| --- | --- | --- |
| `74CA4562` / `40DCC3F4` | Modern / snapshot body map (F:533, F:535) | `Ns::BREP::BRepHistorySerializer` / `Ns::BREP::BRepSerializer` |
| `3B6814F4` | CommonData component-path carrier (F:295) | `Ns::Comp::TransformOverride` |
| `549FBB80` | Direct operation-table poses (F:335) | `Na::DesignCapture::DcOccurrence` |
| `6CCF41D5` | Dimension-presentation frame (F:733) and companion (F:677) | `Na::DesignCapture::DynamicUpdateData` |
| `8C780195` / `855F0A64` | Presentation primary / paired class (F:733) | `Na::FusionSketchLinearDim` / `Ns::Dimension::Dimension` (matches DM:766) |
| `67F4EECB` | Sketch geometry group (F:635) | `SKs::Geometry::MeshPlanarSection`, continuation `Ns::Geometry::GeometryGroup3D` |
| `702B9CD2` / `F85F2E62` | Scene node / mesh Scene-state record (F:551-553) | `Ns::Scene::LayeredTextureMapping` / `Ns::Scene::MeshTextureMapping` |
| `D26351F0` | Body-visibility browser-node member (F:613) | `Na::DesignCapture::DcBody` |
| `E5B3F49A` | Mesh wrapper (F:547) | `NaParaMesh::ParaMeshFacetSelectionHelper` |
| `FA1F0081` | Form body record (F:91) | `NaTSpline::SubDSurfaceNode` |
| `362B7EC3` | Point `paired_reference` companion (F:607) | `Ns::Geometry::CurveUses` |

The class names come from Kit's class catalogue. They do not by themselves refute cadmpeg's functional descriptions. The two texture-mapping matches for "Scene" records are the clearest candidates for re-examination.

## 3. B-rep layer

| Topic | cadmpeg | Kit | Assessment |
| --- | --- | --- | --- |
| Header words | u32 version at 15, zeros 19-31, u64 entity count at 31, u64 flags at 39 (A:15-25) | Four i64: version, optional record count, top-level entity count including `asmheader`, flags (DM:416, BR:248) | Same bytes. Kit's second word is an omitted record count. |
| Revision | `save_format*100 + ((flags>>1)&0x7f)` (A:66) | Same formula, from earlier binary inspection; not confirmed by a black-box experiment (DM:420, BR:248) | Agree, unconfirmed |
| History bit | Bit 0 "set iff the stream carries a history partition"; history streams are selected by this flag (A:23, A:66, F:433, S:352) | Explicit markers are authoritative. Earlier binary inspection said bit 0 cannot prove history is absent; that is not confirmed by a black-box experiment (DM:420-421, BR:248) | **Disagree**, unconfirmed |
| `scale` | Metadata, not a coordinate multiplier (A:67, A:183) | Same for embedded streams (BR:76). Earlier binary inspection said the standalone TemporaryBRep importer rescales by `units/10`; one accepted case agrees, and the rule is not otherwise confirmed (DM:422, BR:250). | Agree; Kit notes a possible importer exception |
| Tags | `0x02`-`0x17`, width 4 or 8 (A:77-102) | Same; Kit's width-4 and rare tags follow cadmpeg (BR:82-104). Tag 23 is an integer only inside one verified schema (DM:443-447). | Agree; Kit is stricter on tag 23 |
| Markers | `Begin-of-ASM-History-Data`; `End-of-ASM-data` has no terminator (A:120-133, A:174) | Same; empty history tail (BR:106-108) | Agree |
| `history_stream` preamble | `stream_size`, `stream_size_duplicate`, 0, `history_entry_count`, with the first two equal (A:139-147) | A rolled-back stream stores `3,10,0,6`, so the first two fields can differ. Kit's names, current and maximum state ID, retained-state limit and next entity tag, came from earlier binary inspection (HS:3, HS:26-30, DM:772) | **Disagree** on equality; the names are unconfirmed |
| `delta_state`, bulletins | Field list; old/new insert, delete and update (A:151-168) | Same fields (BR:183-189). Board scalar is a status enum: mainline, stacked, succeeded, failed (DM:772). | Agree; Kit names the board |
| Materialization | Archived revisions, stable slots, reverse transitions (A:170-174) | Linear journal codec with slot aliases; branches and merges rejected (DM:798-802) | Agree |
| Vertex `index_flag` | 0 = start, 1 = end (A:290) | A native closed circle stores 2; Kit admits 0 and 2 (BR:136, DM:657) | **Disagree**; the meaning of 2 is open |
| `generic_tag_attrib_def` | Body group "entity-class discriminator" 3; face/edge `selector, token, 0, count, refs, 0` (A:330-349, F:577) | Primary byte length, primary text, secondary identity, operation count, operation IDs, approach ID; the length matches the following text in saved documents (GT:10-12, GT:19-28, GT:76-80) | **Disagree**: cadmpeg's 3 is `len("301")` and its 4 is `len("-102")` |
| `sketch_attrib_def` | `(sketch_curve_id, ref_b, sense, enum_a, enum_b)` plus a filler `0` (A:355) | Curve ID, secondary ID, direction (`UINT32_MAX` wildcard), role flags, split ordinal, split total (BR:175, DM:659, DM:667) | Same bytes; Kit names the enums and the "filler" |
| Timestamp attribute | Unix-epoch microseconds (A:357) | Same (BR:163) | Agree |
| Body maps | Match the ASM body key, otherwise use the ordinal among non-sketch-region bodies (F:533) | Match the typed BODY identifier; root order is disproved (DM:456-459, BR:55) | Agree, except for cadmpeg's ordinal fallback |
| Carrier vocabulary | Analytic, NURBS, broad procedural set, tolerant topology (A:361-665, A:292, S:353, S:358) | Plane, cone, ellipse, sphere, torus, planar polyhedra, typed transforms (BR:138-146, DM:730, DM:816-832). Procedural and tolerant forms are open (AE:53). | Gap in Kit |

## 4. Writing

| Aspect | cadmpeg | Kit |
| --- | --- | --- |
| Paths | Three paths: byte replay of an unchanged source; semantic patch of retained source; source-less profile (`crates/cadmpeg-codec-f3d/src/lib.rs:9-11`, `:63-64`). "General writing requires a retained source archive and the original entity and record layouts" (S:385). | One typed emitter. The public route retains "no archive, Design byte block or donor geometry block" (DM:790). |
| Patching | Diffs the target IR against a decoded baseline and patches records in place. It checks completeness with a rebuilt-document digest (W `patch/mod.rs:56-66`) and refuses sources without decoded design intent (`:102`). Patchable families are geometry, topology, sketch points, curves and relations, recipes, persistent references, history states, ACT, materials and visibility (`:45-50`). No parameter or feature-scope patch function was found (**unverified** absence). | Edits change decoded fields and re-emit; there is no offset patching (AE:13). |
| Source-less output | Writes `Manifest.dat`, `Properties.dat`, the asset manifest, one `BREP.generated.smbh`, Design `BulkStream`/`MetaStream`, configurations and Protein appearances (W `generate/mod.rs:88-176`). It refuses SubD, document assets and ACT (`:49-71`) and does not write Browser, OGS or previews. Features, sketches and constraints are `Omitted`; Design history and sketches "come only from native records" (`:183-240`). Parameter owners, scopes, sketch placements and dimension frames are "not writable" (W `generate/records.rs:181`, `:462`). | Complete independent documents for parameter, circle, rectangle, constrained rectangle, circular extrusion, cuboid and frustum profiles. These include all three segments, history, snapshots, materials and graphics, with no source archive or template (AE:9-19, DM:788). |
| Verification | Generated byte fixtures and re-decode goldens (S:387). `write = "verified"` (`crates/cadmpeg-registry/docs/dialect-support.toml:851-853`) means golden artifacts that re-decode, or a stated independent-application gate (`:45-47`). F3D is L5; L9 requires native application acceptance (S:55, S:69). No statement that Fusion opened cadmpeg output was found in the docs or codec (**unverified** absence). | Fusion 2706.1.17 open, rollback, rebuild, parameter edit, save and reopen, with input and output SHA-256 (AE:9-21, AE:71-73). Rows that retain source members are labeled as such (AE:28-30, AE:61, AE:79). |
| Limits | Broad B-rep generation; parametric generation limited as above | Six qualified authoring profiles; other inputs are rejected (DM:788, AE:53) |

## 5. Follow-up for Kit

### 5.1 cadmpeg coverage worth investigating

1. **Cross-document references, XRef placements and pose carriers** (F:283-403, F:488-515, S:378). Kit rejects cross-asset references (`ReadRefMut.py:13`). The bundle codec preserves members without converting their contents (AE:32).
2. **The inline-typed reference generation** (51-byte references, typed parameter tails; F:515, F:659, FO:340 DR-79). Kit's reader has no inline-type branch.
3. **MetaStream variants**: version contexts (F:478-480), differing short and full names (F:468), non-fixed IDs (F:486), early segment end (F:476) and the legacy magic and manifest header (F:244). Kit's checks pin these values (`MetaIndex.py:33-38`).
4. **Configuration tables and rules**, including the active-row root record (F:182-236). Kit supports only empty sidecars (DM:762).
5. **Role codes as observer indices** (§1.1). If they are observer indices, cadmpeg's dimension operand lists name the dimensioned geometry directly.
6. **Feature-scope to journal joins** (F:464, F:765) and the 58-family table (F:771-830). These are relevant to Kit's open feature projection (DM:802).
7. **Persistent-name and recipe resolution to historical topology** (F:559-581; FO:2219 DR-334, FO:2232 DR-462). Kit has typed recipes but no general resolution (DM:673).
8. **ASM procedural, NURBS and tolerant records** (A:292, A:361-665, S:353). Kit lists these as open (AE:53, BR:238).
9. **ParaMesh colour, texture-coordinate and texture channels and `attname.amt.autodesk` XML** (F:142-165). A search of Kit's `re/Fusion/Reconstruction/ParaMesh/WireModel.md` found no colour or texture terms.
10. **T-spline forms that Kit rejects**: deleted slots, extension 106 user knots, radial symmetry, and Form cage joins (F:42-103 vs TS:43-45, TS:72). Re-verify cadmpeg's base labels first (§5.3).
11. **Expression identifier grammar and resolution order** (F:655, final part). Test it against Kit's dependency counterexample (DM:401-404).
12. **The three body bounding-box cache records** (F:531) and the `UnitSystems` collection (F:555-557). Whether Kit's authored documents write the bounding-box records is unverified.

### 5.2 cadmpeg open items that Kit resolves

| Item | Kit answer | Strength |
| --- | --- | --- |
| AO:416 HS-01 | The first two fields can differ, which refutes A:147. Kit reads them as the current and maximum allocated state IDs. | Partial: a rolled-back control shows the difference (HS:26-30, AE:59-61). The names came from earlier binary inspection and are not confirmed by a black-box experiment. |
| FO:356 DR-80 | The u32 is `highWaterMark`; it is not decremented, so it "can exceed" the count. The first reference names `ParameterSearchByNameHelper`, and the final reference names the owning component (DM:231-266). | Reflected member names and controlled captures. The rule that it is never decremented came from earlier binary inspection and is not confirmed by a black-box experiment. cadmpeg's version-3 offsets are four bytes earlier than Kit's layout (F:657 vs DM:235-243); the version correspondence is unverified. |
| FO:1021 DR-144, FO:1507 DR-251, FO:364 DR-81 | Trailer bytes are `isDirty`, `isDriven`, (`isExternal`), `isFavourite`, `isOrphan`, `isUserDefined` (DM:319-343). Null owner with byte 3 set = `isOrphan`. | **Inferred** from member order. It was not checked on cadmpeg's files, and older schema versions are not in Kit's capture (DM:559-566). |
| FO:2219 DR-334 | The token integer is native `secondary_id` (GT:12, GT:26-28, GT:78) | Partial: the name and type are known; the assignment rule is open in both projects |
| FO:620-660 DR-264, DR-288, DR-289 | The class is `SKs::Geometry::MeshPlanarSection` (BC); it backs `DcSketch.meshSections` (DM:612) | Partial: class identity only. Member names may be in Kit's reflection capture (unverified). |
| Uninterpreted MetaStream words (F:468) | Metadata version 8, packed u64 software version, `neutronType`, ancestry count (HM:3-9) | Partial: the names came from earlier binary inspection, which was removed. They are not confirmed by a black-box experiment. |

### 5.3 cadmpeg statements that Kit's evidence contradicts

These are candidates for upstream reports:

- **TSM** (F:40, F:73). Kit's accepted authoring, crease contrasts and edit controls show the following (TS:31, TS:40-47, TS:65-68, TS:70; `Documentation/Changes/Fusion/TSpline/FusionTsplineCodec.md:17`):
  - `l` stores previous before next. Fusion accepted an authored cage with this order.
  - `ec` is not the crease set. Kit's reading of it as an edge index and an end-condition double came from earlier binary inspection and is not confirmed.
  - Namespace 100 changes when an edge is creased, so it is not an editor selection. Kit's reading of namespace 50000 came from earlier binary inspection and is not confirmed.
  - `ver` is a mutation counter.
- **Symmetry maps.** cadmpeg's `f`/`fr` direction labels are the reverse of Kit's (F:75 vs TS:72). Only the label differs.
- The history preamble, generic-tag "selector" and vertex `index_flag` rows of §3.
- The "iff" history flag rule (A:66). Kit's position rests on earlier binary inspection and is not confirmed.
- The MetaStream UUID called "asset GUID" (F:468, F:511) is `currentVersion` per HM:7.
- The "family discriminator" (F:655) is `birthday` per DM:345 (**inferred**).
- `6CCF41D5` is labeled a presentation frame; BC names it `DynamicUpdateData`.

## 6. Why Fusion was hard for both projects

Kit summarizes the problem as several "linked databases inside a ZIP container", each with "a different identity namespace, ordering rule, and versioned schema". Unpacking the ZIP exposes those databases "without resolving their relationships" (DM:38-40). Its difficulty table adds four more points (DM:44-52):

- Class numbers are local to each segment.
- Design IDs differ from kernel entity numbers.
- Cached values repeat parameters.
- "Byte replay cannot prove independent document generation."

cadmpeg's specification records the same hazards as reader failure modes:

- A reader that fixes GUID width "rejects real files" (F:472).
- One that assumes a single reference width "fails on a record that reaches another segment" (F:513).
- Reading the second byte unconditionally "misframes every record carrying a leading block" (F:519).
- Fixed member offsets misframe "exactly those records that happen to carry a property" (F:521).
- Feature names are localized display text (F:769).
- Lost ASM framing shows up as bytes outside the tag table (A:102).

Both projects stop short of replay. cadmpeg states its history "is not yet replayable" (S:360). Kit states that "full arbitrary Fusion interoperability remains unproven" (AE:53).

The methods differ:

- cadmpeg specifications state settled facts without provenance (`AGENTS.md:11`), and its support levels accept evaluations "as stated" (S:38-42). Many frames are keyed on per-file class tags and fixed lengths (about 416 numeric class-tag mentions in F, for example F:1020-1029).
- Kit ties claims to saved documents, runtime reflection and hashed Fusion acceptance runs, and it selects schemas from each archive's registry (DM:570, AE:21).
