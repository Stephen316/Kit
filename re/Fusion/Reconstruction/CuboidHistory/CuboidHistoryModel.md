# Controlled cuboid history model

This specification narrows the next BRep extension to an ordinary solid rectangle extrusion. It specifies the saved solved geometry, persistent identity tags and two-state kernel journal from named fields. It does not establish native acceptance of a new cuboid history writer or of a new parametric rectangle document.

## Evidence and scope

[ControlledHistory.json](ControlledHistory.json) names every field of the 102 initial records in `re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d`. [ControlledDesign.json](ControlledDesign.json) contains the selected Design records that establish the operation, progenitor and sketch identity joins. The scripts [InspectHistory.py](InspectHistory.py) and [InspectDesign.py](InspectDesign.py) read source archives using research decoders, without importing product codecs or calling Fusion.

The native control is a 40 × 30 × 25 mm ordinary extrusion at the origin. Its archived native measurements report a healthy solid with six faces, twelve edges, eight vertices and volume 30 cm³. The archive SHA-256 is `09980af5a2c9e03e0fc9246ed0b20e796c8f5574c8838d255c85bdd08ea1aa9c`; its `.smbh` SHA-256 is `aa25da5b0c1bf72d5ea53cacea4ec09854a0395ebfcfd46786f32480403d0cf2`. The source member is `FusionAssetName[Active]/Breps.BlobParts/BREP.d8acb695-c844-4d75-af4b-55f6fcbac2e7.smbh`.

[CandidateSummary.json](CandidateSummary.json) refines the frozen BRep coverage inventory. All 60 candidate streams across 40 archives have a complete two-state insertion journal with every active record except `asmheader` inserted once. Fifty have the control's exact record count and attribute ownership shape. The remaining ten include different attribute placement, multiple generic groups, transforms, or other operation histories. All 60 are box geometry candidates, not necessarily ordinary extrusion features.

| Observed property | Count |
| --- | ---: |
| Candidate streams / archives | 60 / 40 |
| Complete simple insertion journals | 60 |
| Initial record count 102 | 51 |
| Exact 102-record ordinary attribute shape | 50 |
| Initial record counts 101 / 106 / 103 / 94 / 95 | 1 / 1 / 5 / 1 / 1 |
| Generic groups, all owners | 441 |
| Primary byte-length mismatches | 0 |
| Generic groups with nonzero approach ID | 0 |

The compressed [candidate details](CandidateHistories.json.xz) retain each source path and member digest, all generic groups, sketch tuples, journal prefixes, and insertion IDs. The group counts are 415 single-group attributes and thirteen two-group attributes. Filtering by geometry and journal shape alone must not discard the second group of a Boolean or mirrored body.

## Header, namespaces and boundaries

The qualified header is fifteen ASCII bytes `ASM BinaryFile8`, followed by four little-endian signed 64-bit words `23200, 0, 2, 3`. The saved table has two top-level roots: `asmheader` and one body. The zero stored-record word is not the actual number of initial records. The tagged header follows with three short strings for product, kernel version and save time, then doubles `50`, `1e-6`, `1e-10`. The 50 metadata value is not a blanket multiplier for all geometric fields; the control's embedded position coordinates are centimetres.

The control's `asmheader` record has exactly three fields: attribute reference `-1`, qualified integer `-1`, and kernel version string `232.5.0.65535`. It does not have the ordinary topology three-field prefix plus another version field.

There are four separate identity spaces:

1. Initial ASM record ordinals `0..101`. Tag-12 entity references use these ordinals; `-1` is null.
2. Kernel journal node indices `0,1`. References inside the journal header use this namespace, not the initial record table.
3. Kernel state IDs `4,2`, joined to Design `endModelHS,startModelHS`.
4. Design entity IDs, operation IDs and progenitor tag IDs. These remain separate even when two values happen to be equal.

The current control notably has a Design curve-progenitor entity numbered 301 and an extrusion operation numbered 301. Their numerical equality is incidental; their reference paths establish their meanings.

## Complete initial record classes

There are 86 ordinary records including `asmheader` and sixteen custom attributes. Ordinary topology fields 0–2 are the attribute head reference, saved entity identity integer, and pattern reference. All non-body entity identities in this control are `-1`; the body identity is key zero. Pattern references are null. The record-specific fields follow:

| Type | Count | Fields after ordinary prefix |
| --- | ---: | --- |
| `body` | 1 | first lump, first wire, transform |
| `lump` | 1 | next lump, first shell, owning body |
| `shell` | 1 | next shell, first subshell, first face, wire, owning lump |
| `face` | 6 | next face, first loop, owning shell, qualified null reference, surface, reversed flag, double-sided flag |
| `loop` | 6 | next loop, first coedge, owning face |
| `coedge` | 24 | next, previous, partner, edge, reversed flag, owning loop, qualified zero integer, pcurve |
| `edge` | 12 | start vertex, start parameter, end vertex, end parameter, owner coedge, curve, reversed flag, convexity string |
| `vertex` | 8 | owner edge, owner endpoint index, point |
| `point` | 8 | position |
| `straight-curve` | 12 | origin, parametric direction, optional lower bound, optional upper bound |
| `plane-surface` | 6 | origin, normal, reference vector, V sense, four optional U/V bounds |

All six faces have one four-coedge loop. Every edge has two coedge uses in opposite directions. Twelve straight carriers and six plane carriers complete the geometry. There are no pcurves, transformations, wires, subshells, tolerant entities or nested carrier subtypes in the control. Null and zero fields named as qualified values above have not acquired invented general semantics.

Each optional curve bound is a Boolean token, followed by a double only when true. The four bottom horizontal carriers in the control have finite intervals; the four top horizontal and four vertical carriers are unbounded while their edges have finite intervals. Reading only a nine-field straight-curve form would miss the seven-field unbounded form.

The source linear vertices have owner endpoint index zero for the owner's start vertex and one for its end vertex. Seven indices are one and one is zero. These values must be preserved for source reconstruction. The cylinder's closed-circle index two belongs to a different qualified topology.

Plane reference vectors and line direction vectors are parameterization data. A line satisfies `P(t) = origin + direction*t`; the direction is not necessarily normalized. Plane normal, basis and face sense jointly determine orientation. The control's bottom face uses a positive-Z carrier and a reversed face flag. A new writer can instead use a negative-Z carrier with a forward face, provided its complete coedge orientation and parameterization are consistent.

## Generic tag grammar

The [tag evidence](GenericTagEvidence.json) records the corpus decode of 441 groups. It replaces the previously provisional labels `selector` and `generation reference`:

| Serialized item | Meaning |
| --- | --- |
| Integer before primary text | Primary ID byte length, excluding NUL |
| Primary text | `primary_id` byte string |
| Integer after primary text | Signed `secondary_id` |
| Next integer and that many integers | Ordered `operation_id` array |
| Final integer | Signed `approach_id` |

The same group grammar applies to a body, face or edge. A body group `[3,"301",7,0,0]` means a three-byte primary ID `301`, secondary ID seven, an empty operation array and approach ID zero. The initial three is not a body type discriminator. The five-field body form is simply the zero-operation-array case. A face group `[1,"6",0,1,301,0]` has primary ID `6`, secondary zero, operation array `[301]`, and approach zero.

The primary byte length matches the stored text in all 441 corpus groups, and every approach ID is zero. The field names came from removed static inspection of installed Fusion libraries. They are not confirmed by a black-box experiment.

The width-eight file encodes secondary IDs, operation IDs and approach IDs as signed 64-bit integer tokens. A narrower native width came from the removed static evidence and is not confirmed by a black-box experiment. The inspected names are ASCII. This evidence does not establish general embedded-NUL or arbitrary-Unicode authoring.

Every custom attribute has prefix `REF -1, INT -1, REF next, REF previous, REF owner, STRING family`. Generic attributes then have integers `3,3,-1`, the string `generic_tag_attrib_def ` with its trailing space, a group count, and exactly that many complete groups. The preceding schema integers are distinct from a group's primary byte length.

The control has two chained body attributes: timestamp followed by generic identity. The timestamp payload is integer one and a double authoring timestamp in Unix microseconds. The generic attribute's previous reference points back to the timestamp. All other attributes form one-element owner chains.

## Exact topology tag roles

| Geometric role | Native owner | Primary ID | Operation array | Other identity |
| --- | ---: | --- | --- | --- |
| Body | 1 | `301` | empty | Secondary ID 7 |
| Bottom cap | face 47 | `1` | `[301]` | Secondary / approach 0 |
| Top cap | face 27 | `2` | `[301]` | Secondary / approach 0 |
| X minimum side | face 17 | `3` | `[301]` | Source curve 108 |
| Y minimum side | face 12 | `4` | `[301]` | Source curve 105 |
| X maximum side | face 8 | `5` | `[301]` | Source curve 106 |
| Y maximum side | face 6 | `6` | `[301]` | Source curve 107 |

There are no generic edge attributes in this ordinary rectangle control. In particular, the cylinder's generic top-edge and bottom-edge groups are not required additions to every extrusion.

Each of the four bottom edges has a sketch attribute on both its coedges. A sketch attribute has family `sketch_attrib_def`, integers `1,1,3`, then one counted ASCII tuple: `primary secondary direction topologyRoleFlags splitSequence splitTotal`. The control tuples are `105 0 0 0 1 1` through `108 0 0 0 1 1`. These point at the originating sketch curves, not ASM records 105–108. The two coedges of each edge carry identical tuples even though their coedge reversed flags differ.

Let rectangle corners A=(0,0), B=(W,0), C=(W,D), D=(0,D). The source boundary curves are A→B tag105, B→C tag106, C→D tag107 and D→A tag108. A new geometry writer that stores all edges from lower corner number to higher corner number changes two of these carrier orientations. It must coordinate its explicit source-curve directions and sketch-link direction fields with its independently generated Design profile; it must not derive a sketch direction merely from the coedge reversed flag. That coordination still requires native rebuild acceptance.

## Design joins, not integer coincidence

The decoded control establishes these relationships:

| Design record | Joined fields |
| --- | --- |
| BRep history serializer 8 | `mapBodyId` maps ASM body key 0 to Design body 311; `partName` selects this `.smbh` |
| Feature-ID manager 31 | Sketch entity 207 owns operation 300; extrusion entity 279 owns operations 301 and 302 |
| Extrusion 279 | `startModelHS=2`, `endModelHS=4`; progenitor table 298 |
| Progenitor table 298 | Curve progenitors 301/303/305/307 have tags 3/4/5/6; body progenitor 310 has tag 7; next tag 8 |
| Body progenitor 310 | Body UUID `e33c6998-78e9-406e-98ad-0ab8ad6e0b23`; primary-name data ASCII `3456`, offsets `[0,1,2,3,4]`, operation 301, occurrence count 1 |

Thus the body generic secondary ID seven equals the body-progenitor table tag, while the four side primary names equal their corresponding curve-progenitor tags. This is an observed cross-record join in this control, reinforced by the earlier circle control's body secondary four/body-progenitor tag four. It is not a proof that every body's secondary ID is always its largest face name plus one; imports, Booleans and reparenting require their actual identity data.

The four curve recipes hold direction-one sketch tags, split pair `(1,1)` and zero topology role flags. Their endpoint-adjacent tag sets are:

| Side primary name | Source tag | Start-adjacent tag | End-adjacent tag |
| --- | ---: | ---: | ---: |
| `3` | 108 | 107 | 105 |
| `4` | 105 | 108 | 106 |
| `5` | 106 | 105 | 107 |
| `6` | 107 | 106 | 108 |

The JSON research decoder still uses `objectOffset20Set` and `objectOffset38Set`; Kit names them start- and end-adjacent primary tag IDs; see [SketchTagSemantics.md](../EntityGraph/SketchTagSemantics.md). That naming is not confirmed by a black-box experiment. The region recipe's native type is `std::list<std::pair<std::list<sketch_tag_id>,bool>>`. The control stores the ordered tag list 107,106,108,105, all with direction zero and split pair `(1,1)`, paired with Boolean true. That observed order is not the geometric perimeter order. Nothing proves that list order is semantically interchangeable, so source reconstruction must retain it and independent authoring must establish its own accepted ordering. The endpoint-adjacent collections remain sets.

## Two-state journal

The `Begin-of-ASM-History-Data` name chain is immediately followed by the `history_stream` name chain. Its eight fields are:

```text
INT generation=4, INT generationDuplicate=4, INT zero=0,
INT allocation=1, REF -1, REF currentNode=0, REF initialNode=1, REF -1
```

Generation and allocation remain explicitly supplied kernel metadata. Their complete allocation algorithm is not established here. The control's allocation value is one and body key zero; source lineages can change these after native recomputation.

The current delta state contains 318 fields:

```text
INT stateId=4, INT versionFlag=1, INT stateFlag=0,
REF previousNode=-1, REF nextNode=1, REF nodeIndex=0,
REF partner=-1, REF owner=0, FALSE,
INT boardPresent=1, REF boardOwner=0, INT boardNumber=2,
101 × (INT changePresent=1, REF oldRevision=-1, REF newInitialOrdinal),
INT changesEnd=0, INT boardsEnd=0, INT stateEnd=0
```

The new ordinals are exactly the set `1..101`, each once. Their serialization order need not be the source's allocation order; the existing reader checks complete membership and uniqueness. The old revision is null because every change is insertion. Reversing these changes removes every active entity except `asmheader` at ordinal zero.

The initial delta state has eleven fields:

```text
INT stateId=2, INT versionFlag=1, INT stateFlag=0,
REF previousNode=0, REF nextNode=-1, REF nodeIndex=1,
REF partner=-1, REF owner=0, FALSE,
INT boardsEnd=0, INT stateEnd=0
```

`End-of-ASM-History-Section` and `End-of-ASM-data` are consecutive final name chains with no intervening record terminator. There are no archived geometry revisions in this profile. The two-state insertion journal is kernel membership history; the editable sketch, feature and parameter history remains in Design.

## Independent authoring recipe and promotion path

The writer's inputs are width, depth, height, base placement, fresh body key and UUID, extrusion operation ID, four source-curve identities and directions, six face primary names, body secondary ID, authoring time, provenance strings and explicit journal state metadata. The Design author supplies the same operation/progenitor IDs and the enclosing BRep part basename. No source archive, source token table, raw attribute, opaque payload or fixed native entity ordinal is an input.

1. Construct eight corners from dimensions and placement. Generate the six outward face loops, twelve edges and their two directed uses, eight vertices, twelve straight carriers and six plane carriers. Allocate all records freshly. The current `GeometryCodec/Prism/CuboidRecords` layout uses roots 0–3, faces 4–9, loops 10–15, coedges 16–39, edges 40–51, planes 52–57, vertices 58–65, curves 66–77 and points 78–85. The record graph is newly computed; these ordinals are a writer allocation policy, not required native ordinals.
2. Append body timestamp at 86 and generic identity at 87. Set body attribute head 86, timestamp next 87, generic previous 86 and both owners to body 1. Set body key from the semantic input.
3. Append six face attributes at 88–93. The current Prism face order is bottom, top, Y minimum, Y maximum, X minimum, X maximum, so the controlled naming pattern is primary IDs `1,2,4,6,3,5`. A caller can supply the corresponding fresh progenitor names explicitly. Each face has secondary zero, operation array containing the extrusion operation, and approach zero.
4. Append eight sketch attributes at 94–101, two per bottom edge, and set their coedge heads. Find owners by edge/corner roles, not native ordinal copying. Retain the complete semantic source tuple, including split pair and direction. There are no extra generic edge attributes in this qualified authoring profile.
5. Derive every group's primary byte length and operation count. Serialize its complete typed fields. Emit the header with history flag three, then all 102 initial records. Append the two-state journal with insertion count 101 and the exact end-marker grammar. The existing parameterized `History/EmitJournal` and `Reading/ReadJournal` can serve this shape; cylinder-specific `HistoryRecords`, `KHistoryHeads`, `ReadCylinder` and `ReadTagSet` cannot.
6. Promote a typed cuboid history result that preserves semantic dimensions/placement, carrier parameter frames, vertex owner endpoint indices, all attributes and explicit journal state. Source reconstruction must retain native ordering/provenance when necessary; a new writer may use its own consistent allocation and parameterization. Reject unknown or extra records instead of silently retaining source bytes.
7. After standalone cuboid geometry acceptance, have the parent serialize this history into an independently authored rectangle Design graph. Observe initial geometry before `computeAll()`, rollback to sketch only, restore, edit a driving dimension, rebuild, save and reopen. Rectangle sketches need four lines, endpoint/constraint relationships, a closed-region recipe and four curve progenitors; a cylinder graph plus a box cache is not a parametric box document.

| Existing cylinder profile | Controlled box profile |
| --- | --- |
| 26 plain records | 86 plain records |
| 9 attributes | 16 attributes |
| 35 initial records / 34 insertions | 102 initial records / 101 insertions |
| 3 face generic tags | 6 face generic tags |
| 2 edge generic tags | No edge generic tags |
| 2 coedge sketch links to one curve | 8 links to four curves |
| Body secondary ID 4 in native control | Body secondary ID 7 in native control |
| One curve progenitor | Four curve progenitors with adjacent-tag sets |

All generated-writer steps above are an implementation recipe. The actual observations in this document are read-only decoding of archived source files. Claims from removed static library inspection are marked as not confirmed by a black-box experiment. Product and vendor acceptance must be recorded separately.
