# Fusion BRep Wire Model and Independent Cylinder Authoring

## Status and evidence boundary

This investigation completely frames every byte of the two BRep streams in the local native `extrude_07mm.f3d` control. Reencoding their typed scalar, string, vector, name and delimiter tokens reproduces both streams byte for byte. This establishes the observed binary grammar, not an independently authored general-purpose Fusion file.

A separate writer authors a new cylinder from radius, height and origin, with a new record allocation and no read of a native file. It emits both standalone SMT text and ASM binary. Fusion 2706.1.17 accepted the independent SMT, measured the expected solid, saved it as native F3D and reopened it with identical measurements. Fusion also accepted the unchanged binary through its documented temporary BRep API, then retained all measured geometry after adding the body to a native direct design, saving and reopening it. Neither generated artifact contains the Fusion Design feature graph, body-map links or a parametric history. They are research solids, not production-ready F3D conversions.

The input cylinder has radius 10 mm, height 7 mm and base center `(0, 0, 0)` mm. The independent cylinder deliberately has radius 15 mm, height 11 mm and base center `(20, -30, 5)` mm. Its output does not preserve vendor attribute records, UUIDs, file metadata, record order or opaque fields.

## Sources and attribution

The wire interpretation was informed by the [cadmpeg ASM format specification](https://github.com/cadmpeg/cadmpeg/blob/de2726870ff728352163f601ab4e60bbd54fbade/docs/formats/asm.md) and [Fusion format specification](https://github.com/cadmpeg/cadmpeg/blob/de2726870ff728352163f601ab4e60bbd54fbade/docs/formats/f3d.md), pinned at commit `de2726870ff728352163f601ab4e60bbd54fbade`. These specifications are licensed CC-BY-4.0; attribution belongs to the cadmpeg project. This document adapts and narrows those specifications using the native control observations below. It does not claim upstream completeness as local verification. The upstream code is Apache-2.0. No upstream code or vendor file payload is embedded in the independent cylinder writer.

Native control evidence:

| Artifact | Meaning | SHA-256 |
|---|---|---|
| `LocalOracle/Features/extrude_07mm.f3d` | Locally authored parametric native cylinder | `ff7730152b56ef608e690df79788ee5658473d59b33e398dc96743e306adacd1` |
| `LocalOracle/Brep/cylinder_07mm.smt` | Native SMT export from that archive | `7b84db7cb8b30b7d708cd3cdace0d11009ffc9029ce5c0dd72a1040f624801d2` |
| `LocalOracle/Brep/Export.json` | Native export execution and provenance | Parent-owned report; preserve verbatim |
| `LocalOracle/Brep/Acceptance.json` | Native independent-SMT import, F3D save and reopen evidence | Binds source SHA-256 `5f762eece03e2504f7d5777cd6ed4efa048ba0542d806a5ea9daafd98e4f3a83` |

All relative paths in this document are under `re/Fusion/`. The export report ends with a license restriction on a subsequent SAT export. The SMT export preceding it succeeded. SAT is not needed for this investigation; its restriction was not bypassed.

Derived evidence and tools:

The four verbose token, semantic, and derivation JSON reports listed below are preserved byte-for-byte in [BrepEvidence.tar.xz](../LocalOracle/Brep/BrepEvidence.tar.xz).
The [digest index](../LocalOracle/Brep/BrepEvidence.json) records each filename, size, SHA-256, and extraction command.
The research commands below also regenerate the uncompressed reports.

| File | Function |
|---|---|
| `Reconstruction/BrepTokens.py` | Complete bounded token framing and typed binary serialization |
| `Reconstruction/BrepModel.py` | Named fields, native attribute groups and the observed insertion journal |
| `Reconstruction/BrepWire.json` | Observed class signatures, counts and unresolved identities |
| `Reconstruction/BrepCylinder.py` | Semantic cylinder model and independent SMT serializer |
| `Reconstruction/BrepCylinderBinary.py` | Independent binary serialization of the same semantic cylinder |
| `LocalOracle/Brep/extrude_07mm.tokens.json` | Every token's byte offset, extent, discriminator and value |
| `LocalOracle/Brep/extrude_07mm.semantic.json` | Every observed initial record's named fields and history state membership |
| `LocalOracle/Brep/kit_cylinder_15r_11h.derivation.json` | SMT field-by-field derivations and expected native measurements |
| `LocalOracle/Brep/kit_cylinder_15r_11h.binary-derivation.json` | Binary field tags, values and unit conversions |

## Container and geometry partition

The archive contains two complete binary kernel streams:

| Member basename | Bytes | Header words | Initial records | Bodies | Role |
|---|---:|---|---:|---:|---|
| `BREP.6b7f67e0-2eb6-4db1-9a3c-b5d54f9a9fe5.smb` | 6039 | `23200, 0, 4, 2` | 59 | 3 | Snapshot containing the cylinder and planar sketch/profile bodies |
| `BREP.d86a1a4b-6c08-43f7-a387-60ee0f06ff59.smbh` | 5300 | `23200, 0, 2, 3` | 35 | 1 | Solved cylinder plus an ASM transaction journal |

The snapshot is not a second independent model to union with the solved cylinder. Its first body has three faces, and its other two bodies each have one planar face. One of those planar faces is double-sided. Counting all BRep bodies in the archive would count profile/cache state as output geometry.

The upstream Fusion schema selects modern model blobs through Design body-map carriers with type GUID `74CA4562-59F8-4C97-8AD1-F8297C21F9AA`. The blob basename scopes each selector namespace. A selector first matches a nonnegative ASM body key; otherwise it selects the eligible body ordinal. Modern maps select the `.smbh` model set; snapshot maps do not add model bodies when modern maps exist. The local parent investigation owns independent Design-carrier verification.

The initial production `AsmTable.py` admitted only flags `3` and stopped at the history marker. It now also admits the observed flags-`2` profile and returns a no-history table at `End-of-ASM-data` only when the marker reaches EOF. The existing history path still returns the initial table; it does not interpret the journal. A full reader must separate stream framing, active model selection, kernel history and Design feature history.

## Binary envelope

The observed streams begin with the 15 ASCII bytes `ASM BinaryFile8`, immediately followed by four signed little-endian 64-bit words. There is no separator byte after the magic.

| Offset | Width | Field | Observed values |
|---:|---:|---|---|
| 0 | 15 | Magic | `ASM BinaryFile8` |
| 15 | 8 | Save-format version | 23200 |
| 23 | 8 | Stored record count | 0 |
| 31 | 8 | First owned record boundary | 4 in snapshot, 2 in history stream |
| 39 | 8 | Flags | 2 or 3 |
| 47 | Variable | Product, version, date, scale, absolute tolerance, normal tolerance | Six typed tokens |

The fourth word is not a body count. `asmheader` is record 0. In the snapshot, bodies occupy records 1, 2 and 3; the first owned lump is record 4. In the history stream, the sole body is record 1 and its first owned attribute is record 2. Flags bit 0 indicates history; shifting right by one gives revision 1 in both controls.

The six header tokens are tags `7, 7, 7, 6, 6, 6`. The actual strings are `Autodesk Neutron`, `ASM 232.5.0.65535 OSX` and the native save date. The two tolerances are `1e-6` and `1e-10`.

The binary scale is 10 in the snapshot and 50 in the history stream, while both store cylinder radius 1 and height `0.7000000000000001`. Both represent the same native radius 10 mm and height 7 mm. This directly demonstrates that the binary header scale is not a multiplier for model coordinates. Binary points and length-bearing vectors use centimetres in this profile.

## Typed token grammar

The parser keeps the discriminator independently from the decoded value. An integer-looking text representation is insufficient to recover a binary type. For example, direction components, point coordinates and radius ratios may all print `1` but have different tags and unit semantics.

| Decimal tag | Payload | Semantic role |
|---:|---|---|
| 2 | One unsigned byte | Small scalar |
| 3 | Signed little-endian 16-bit integer | Short scalar |
| 4 | Signed integer of stream width | Entity identity, count or profile integer |
| 5 | IEEE 32-bit float | Scalar |
| 6 | IEEE 64-bit float | Scalar or length, selected by field |
| 7 | Unsigned 8-bit byte count, then UTF-8 | Short string |
| 8 | Unsigned 16-bit byte count, then UTF-8 | Medium string |
| 9, 18 | Signed stream-width byte count, then UTF-8 | Long string |
| 10, 11 | None | True and false |
| 12 | Signed integer of stream width | Reference in the applicable record namespace |
| 13 | Unsigned 8-bit byte count, then UTF-8 | Leaf identifier |
| 14 | Unsigned 8-bit byte count, then UTF-8 | Prefix identifier |
| 15, 16 | None | Open and close subtype scope |
| 17 | None | End of record |
| 19 | Three IEEE 64-bit values | Position |
| 20 | Three IEEE 64-bit values | Direction or length-bearing vector |
| 21 | Signed integer of stream width | Enumeration |
| 22 | Two IEEE 64-bit values | UV vector |
| 23 | Signed 64-bit integer, even in width-4 streams | Wide attribute scalar |

Only a subset occurs in the native cylinder. The parser's width-4 and rare-tag implementations follow the pinned specification and are not locally evidenced by this one sample. `BrepWire.json` preserves the actually observed tag signatures rather than presenting the full tag vocabulary as measured coverage.

Record names are chains of tag-14 prefixes ending in one tag-13 leaf. `cone-surface` is therefore two name tokens. Normal records end with tag 17 at subtype nesting depth zero. The final `End-of-ASM-data` marker ends at EOF without tag 17.

History markers are structural prefixes. `Begin-of-ASM-History-Data` is followed directly by a second leaf `history_stream`. In this control, the empty archived-revision section ends with `End-of-ASM-History-Section` immediately followed by `End-of-ASM-data`, with no delimiter between their name chains. A reader that requires every name chain to have its own terminator incorrectly rejects this valid empty history tail.

`BrepTokens.py` accounts for all 6039 snapshot bytes and all 5300 history bytes. It serializes from typed values rather than storing or appending raw record blocks. Its byte identity result proves lexical coverage of the source data only. A source-token round trip does not meet the independent authoring requirement.

## Active record model

The basic modern entity prefix is an attribute reference, an integer identity/history slot and a nullable reference. All observed nonattribute values of the third slot are null. Calling the third slot a fully understood universal field would overstate the evidence.

The following field lists begin after that three-field prefix:

| Class | Remaining fields in order |
|---|---|
| body | first lump, first wire, transform |
| lump | next lump, first shell, owner body |
| shell | next shell, first subshell, first face, wire, owner lump |
| face | next face, first loop, owner shell, reserved reference, surface, sense, sidedness, conditional containment if double-sided |
| loop | next loop, first coedge, owner face |
| coedge | next, previous, partner, edge, sense, owner loop, integer, pcurve |
| edge | start vertex, start parameter, end vertex, end parameter, owner coedge, curve, sense, convexity string |
| vertex | owner edge, edge index, point |
| point | model-space position |

`asmheader` is special: attribute reference, identity/history integer, version string. Attribute records have a different prefix: reserved reference, marker integer, next attribute, previous attribute and owner. Their third field is a real forward attribute link, not the null entity-prefix field.

Every initial nonnegative entity reference in both native streams resolves within its initial table. This excludes journal node references and Design identities, which belong to different namespaces.

The top and bottom circle edges each use one vertex for both ends, with parameters `-pi` and `pi`. The cylinder has no vertical seam edge. The side face has two loops, each containing a self-linked coedge. Each cap has one loop. Coedges are paired across the side/cap boundary, and their senses oppose one another. Top and side faces are forward; the bottom face is reversed.

The native top vertex has edge-index value 2. The bottom vertex has value 0. The upstream description of this field as a 0/1 endpoint choice is insufficient for this modern closed-circle control. The independent writer chooses the observed start-reference value 0 for both vertices. It does not silently reinterpret source value 2 or claim its meaning is resolved.

## Analytic geometry

The cylinder surface is a `cone-surface` specialized to zero half-angle. After the entity prefix it stores origin, axis, radius vector, ellipse ratio, two optional ellipse bounds, sine and cosine of the half-angle, a parameter length scale, sense and four optional parameter bounds. The observed cylinder has sine 0, cosine 1 and ratio 1. All optional bounds are absent and therefore encoded as false tokens.

An `ellipse-curve` stores center, normal, radius vector, ratio and two optional bounds. Ratio 1 makes a circle. The edge interval supplies the full-circle traversal; the unbounded analytic carrier and trimmed edge interval are separate objects.

A `plane-surface` stores origin, normal, reference vector, V sense and four optional bounds. The native binary reference vector is `(1, 0, 0)` and the native SMT exporter emits `(10, 0, 0)`. This illustrates why parameter frames must be treated separately from positions and circle radius vectors. The independent model chooses a unit X reference frame explicitly. Native acceptance demonstrates this chosen frame is valid for the independently generated cylinder; it does not establish the exporter's general parameter-frame transformation rule.

The point record supplies vertex coordinates; the vertex's owner-edge reference does not contain coordinates. For this circle, the point is the analytic curve evaluated at `-pi`, including the small floating-point sine residue. The writer derives that value with `sin` and `cos`; it does not copy the native residue.

## Attribute and identity model

Several different IDs coexist. They are not interchangeable integers:

1. Physical record order in the complete stream, including journal records.
2. Initial topology record references.
3. History node references and state identifiers.
4. Old/new record revisions in the journal.
5. The body key in the body's integer slot.
6. Persistent Design IDs in counted strings.
7. Indexed Design record references in attribute groups.
8. Sketch primary/secondary curve identities.

In the history stream, body record 1 has body key 0. Its first attribute is record 2, a timestamp, whose next link points to record 4, the persistent Design link. The reverse link from attribute 4 returns to attribute 2, and both owners are body 1.

`Timestamp_attrib_def` has marker 1 followed by a double containing `1794477991119457` microseconds since the Unix epoch. This is independent of the file header save date.

`generic_tag_attrib_def` begins with integers `3, 3, -1`, a repeated family string with a trailing space, and a group count. The string's trailing space is payload, not alignment padding. The 441 decoded corpus groups show the same group grammar for every owner class: primary byte count, primary counted text, secondary identity, operation count and ordered operation identities, then approach identity. The names of the secondary and approach identities and their signed width came from earlier binary inspection; no black-box experiment confirms them. The earlier class-selector and generation-reference interpretation was incorrect; [the corpus evidence](CuboidHistory/GenericTagEvidence.json) and [semantic correction](../../../Documentation/Changes/Fusion/FusionGenericTagSemantics.md) supersede it.

| Owner | Group fields | Control values |
|---|---|---|
| Body | primary byte count, primary text, secondary identity, empty operation count, approach zero | `3, "301", 4, 0, 0` |
| Face | primary byte count, primary text, secondary zero, operation count, operations, approach zero | Side/top/bottom tokens `"3"`, `"2"`, `"1"`; each refers to 301 |
| Edge | primary byte count, primary text, secondary zero, operation count, operations, approach zero | Top token `"-1"`, bottom token `"-102"`; each refers to 301 |

The negative string tokens are not null references. Their serialization is tag 7 UTF-8, not tag 12. The exact naming rule for arbitrary topology-changing operations remains unresolved.

`sketch_attrib_def` identifies source curves. The observed form has marker integers `1, 1, 3` and one string containing `102 0 0 0 1 1`. Its fields are primary curve ID 102, secondary curve identity 0, direction 0, topology role flags 0, split ordinal 1, and split total 1. Snapshot sketch edges also have direction 1 variants; native comparison admits UINT32_MAX as a direction wildcard. [Native ASCII evidence](EntityGraph/SketchAsciiSemantics.md) establishes unsigned widths and distinguishes this order from the binary Design callback. The attribute connects topology to an originating sketch; it does not define the circle geometry. An independent primitive with no originating Design sketch must not borrow this identity.

The native SMT export removes these persistent generic tags, inserts `DXID-attrib` labels `"ASM ENTITY"` with sequential strings, and attaches a direct RGB attribute. It retains the timestamp and some sketch links. Therefore SMT export is a geometry interchange projection, not an identity-preserving serialization of the entire embedded stream. Reimporting it cannot by itself establish parametric feature/history round-trip preservation.

## Observed journal

The active table is followed at byte 3964 by `history_stream`. Its eight typed fields are integers `4, 4, 0, 1` and references `-1, 0, 1, -1`. The first two integers agree, but they are not byte lengths: the complete stream is 5300 bytes. The preamble entry count is 1 while there are two delta states. This control alone cannot establish a universal counting interpretation.

At byte 4084, current `delta_state` has state ID 4, markers 1 and 0, previous node -1, next node 1, node index 0, reserved reference -1, reference 0 and a false sentinel. It contains one bulletin board with owner 0 and board number 2.

Every change has an integer presence marker followed by old and new references. All 34 changes in this control are `-1 -> slot`, inserting precisely initial record slots 1 through 34. Their order reflects construction/registration order rather than numerical order. Reversing the board removes every live entity except `asmheader` at slot 0.

At byte 5143, the previous `delta_state` has state ID 2, previous node 0, next node -1 and node index 1. Its bulletin chain is empty. The final marker begins at byte 5248 and contains no archived entity revisions.

The bulletin grammar is nested: a board presence integer, owner reference and board number precede change presence/old/new triplets. Zero closes the change chain; zero closes the board chain; one final zero separates the state from the next record. The empty state's tail has only the board-chain zero and final zero.

This journal is kernel entity creation history. It is not the Design timeline's editable sketch and extrusion feature model. The initial state IDs 2 and 4 do not establish feature IDs. A general history reader additionally needs archived-revision namespaces, update/deletion materialization and stable-slot remapping. The local model explicitly limits its membership reconstruction to the observed insertion case.

## Independent writer design

`BrepCylinder.py` accepts only semantic dimensions and an output path. Its constructors allocate 26 records:

| Records | Allocation |
|---|---|
| 0–3 | Header, body, lump, shell |
| 4–6 | Side, top and bottom faces |
| 7–10 | Two side loops, top loop, bottom loop |
| 11–14 | Four coedges |
| 15–16 | Top and bottom edges |
| 17–19 | Cylinder surface and cap planes |
| 20–21 | Top and bottom vertices |
| 22–23 | Top and bottom circle carriers |
| 24–25 | Top and bottom point geometry |

Every reference is assigned from this allocation. Every numeric geometry value is derived from the input cylinder, a mathematical constant or the chosen coordinate frame. Every structural null, absent bound, orientation, format version and terminator has a named derivation. No template blob, native archive, base64 data or opaque suffix is read.

The text header declares `Kit`, `Independent SMT research`, a fixed research timestamp, save format 23200, top-level root count 2 including `asmheader`, flags 2, and a length scale of 1 mm per unit. Its counted strings use UTF-8 byte lengths. Fields use `$N` for references and `@N` for counted payloads. Text floats are emitted with 17 significant digits.

The binary writer serializes the same model using typed field tags. Explicitly named `_mm` length fields convert to centimetres. Positions receive tag 19, reference/direction/radius vectors tag 20, scalar lengths tag 6, references tag 12 and profile integers tag 4. The dimensional role comes from the model field, not the numeric spelling or vector tag alone.

The independent SMT artifact is 1369 bytes, SHA-256 `5f762eece03e2504f7d5777cd6ed4efa048ba0542d806a5ea9daafd98e4f3a83`. The binary artifact is 2396 bytes, SHA-256 `e543149d548412263728f3c33cabf115badbbc459d43e5a124a8df8f62d2e407`.

Expected native measurements are one solid body, three faces, two edges and two vertices; volume `7.775441817634738` cm³; center of mass `(2, -3, 1.05)` cm; minimum bounding point `(0.5, -4.5, 0.5)` cm and maximum `(3.5, -1.5, 1.6)` cm.

The native [Acceptance.json](../LocalOracle/Brep/Acceptance.json) records a solid with exactly three faces, two edges and two vertices. Its volume is `7.7754418176350715` cm³, differing from the analytic value by approximately `3.34e-13` cm³. Its center is `(2.0000000001568523, -3.0000000000000004, 1.0500000000000003)` cm, and both bounding corners match the analytic values. These observations remain identical after Fusion saves and reopens a native F3D, SHA-256 `232920ff6a315fa7281b4c2139756618721dda221a1141a01145b401f930e0d4`.

This evidence also shows the attribute-free graph and vertex edge-index value 0 are accepted for this cylinder. It does not identify the meaning of the source control's value 2. The native application was used only for acceptance, not generation. No parametric extrusion feature was generated by the SMT writer.

## Reproduction commands

Run from the isolated repository root. These commands generate and analyze research artifacts; they do not invoke a test suite or a CAD runtime.

```sh
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepTokens.py re/Fusion/LocalOracle/Features/extrude_07mm.f3d re/Fusion/LocalOracle/Brep/extrude_07mm.tokens.json
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepModel.py re/Fusion/LocalOracle/Brep/extrude_07mm.tokens.json re/Fusion/LocalOracle/Brep/extrude_07mm.semantic.json
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepCylinder.py re/Fusion/LocalOracle/Brep/kit_cylinder_15r_11h.smt
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepCylinderBinary.py re/Fusion/LocalOracle/Brep/kit_cylinder_15r_11h.smb
```

Python 3.14 is required here for the archive's ZIP compression method 93. Standalone kernel token parsing and cylinder generation do not themselves require that ZIP feature.

## Remaining acceptance work

Native SMT import, geometry inspection, F3D save and reopen are established for the independent cylinder. Binary geometry import and native save/reopen are also established; parametric edit/rebuild evidence remains separate. Parametric acceptance must address the Design feature graph rather than treating an imported body as an editable extrusion. Arbitrary BRep support additionally requires tolerant topology, NURBS, procedural carriers, intersections, pcurves, trims, transforms, nonmanifold uses and full history revision handling. Their absence is a capability limit, not an unknown opaque-byte shortcut.

Before production promotion, replace this research code's bounded observational profiles with validated typed structures, preserve every applicable source feature and identity, implement the surrounding native Design/carrier graph, and obtain target-application load/edit/rebuild evidence on independently authored outputs. The detailed field evidence here supports that work but does not waive those requirements.

## Binary import route and native header semantics

The unchanged 2,396-byte binary was accepted through `TemporaryBRepManager.createFromFile` with its `.smb` extension. The text-only `createSMTImportOptions` API first rejected `.smb`; renaming the bytes to `.smt` passed extension validation but selected the text parser and failed import. Neither failure established invalid binary grammar. The [native binary acceptance](../LocalOracle/Brep/BinaryTemporaryAcceptance.json) binds the successful source digest and saved native archive.

The temporary body reported the correct solid topology, volume and bounds, but `physicalProperties.centerOfMass` returned `(0, 0, 0)`. After inserting that same body into a direct design, the center became `(2.0000000001568523, -3.0000000000000004, 1.0500000000000003)` cm and remained so after save/reopen. The strict center check applies to those persistent observations; the temporary discrepancy is retained rather than treated as a geometry failure.

The accepted header has a third integer of 2, which matches its two top-level roots: `asmheader` and the body. Fusion accepted a second integer of zero. Earlier notes derived a format-revision formula from the flags word and said bit 0 cannot prove history is absent. Those rules came from binary inspection and are not confirmed by a black-box experiment. Explicit history markers are the reliable sign of journal presence.

The independently generated binary encodes centimetre length values with units metadata 10, and Fusion accepted the expected physical size. Earlier notes said the temporary BRep importer rescales by `units / 10`; that rule is not confirmed beyond this case. The embedded history control's metadata 50 must be interpreted in its owning restore path; a blanket scale assumption across standalone and embedded loaders is not established.
