# Independent Embedded Cylinder History Authoring

## Archived field evidence

The verbose generated JSON reports are preserved exactly in [HistoryEvidence.tar.xz](HistoryEvidence.tar.xz); [HistoryEvidence.json](HistoryEvidence.json) lists their original filenames, sizes, SHA-256 digests, and extraction command. The report names below refer to those archive members. Native acceptance reports remain separate readable files.

## Scope

This experiment authors the complete solved-model `.smbh` stream for a 19 mm extrusion of a 10 mm radius circle. It accepts explicit Design identity values and an insertion-only kernel history model. It does not read a native archive, native kernel stream or recorded payload during generation.

The intended enclosing document is the same-source `extrude_07mm.f3d` whose editable extrusion parameter/feature payload has already been changed to 19 mm by the parent investigation. Replace only its existing solved-model member `FusionAssetName[Active]/Breps.BlobParts/BREP.d86a1a4b-6c08-43f7-a387-60ee0f06ff59.smbh` with the generated stream. Keeping the basename preserves the existing body-map carrier. The experiment asks whether the saved BRep geometry is 19 mm immediately on native open, before `computeAll()`, and whether a later edit/rebuild to 23 mm works.

Native acceptance now establishes this same-source geometry/cache edit with a newly authored BRep and kernel journal: Fusion opened the model at 19 mm before rebuilding, then accepted a 23 mm feature edit, rebuild, save and reopen. It does not establish independent authoring of the surrounding Fusion Design feature graph or general F3D conversion.

## Files

| File                                  | Role                                                                              |
| ------------------------------------- | --------------------------------------------------------------------------------- |
| `IdentityModel.py`                    | Typed body, topology tag, sketch link, journal and provenance inputs              |
| `AttributeRecords.py`                 | Newly allocated persistent, sketch and timestamp attributes                       |
| `JournalRecords.py`                   | Explicit two-state insertion journal                                              |
| `GenerateHistory.py`                  | Complete ASM binary serialization and per-field derivation report                 |
| `CylinderNineteen.json`               | Explicit semantic input for this same-source edit                                 |
| `IndependentNineteen.smbh`            | Generated 5,286-byte stream                                                       |
| `IndependentNineteen.derivation.json` | Every record/field derivation and input provenance                                |
| `IndependentNineteen.tokens.json`     | Full byte-offset token framing of the generated stream                            |
| `IndependentNineteen.semantic.json`   | Named entity, attribute and journal fields                                        |
| `NativeLineage.json`                  | Native 7 mm, 13 mm and two 23 mm stream identity observations                     |
| `CacheMeasurements.json`              | Independently calculated 19 mm area, volume, centroid and inertia                 |
| `AcceptanceBinding.json`              | Exact generated-geometry and enclosing-archive hashes linked to native acceptance |

The generated stream's SHA-256 is `077ab663e22ea712f58c9745466c2035bd62ba496933da84668a708fa2d347c2`.

## Source facts and attribution

The schema investigation uses the pinned [cadmpeg ASM specification](https://github.com/cadmpeg/cadmpeg/blob/de2726870ff728352163f601ab4e60bbd54fbade/docs/formats/asm.md), licensed CC-BY-4.0 with attribution to the cadmpeg project. These adapted findings narrow that specification using native locally authored documents and native entity reflection. The associated open-source code is Apache-2.0. Generation imports the independent research cylinder model and typed token serializer; it does not import or embed upstream serializer code or vendor payloads.

Native controls and reflection are analysis inputs only. `GenerateHistory.py` reads exactly the semantic JSON input supplied on its command line and writes a newly constructed stream and derivation report.

## Identity joins verified in the native control

These identities come from `LocalOracle/Features/extrude_07mm.entities.json` and the fully framed embedded kernel stream:

| Namespace                 |   Identity | Observed relationship                                  |
| ------------------------- | ---------: | ------------------------------------------------------ |
| Design indexed record     |          8 | `Ns::BREP::BRepHistorySerializer`                      |
| Design indexed record     |          7 | Current `Ns::BREP::Bodies` collection                  |
| Design indexed record     |        261 | `Ns::BREP::Body` owned by collection 7                 |
| ASM body key              |          0 | `mapBodyId` in record 8 pairs key 0 with body 261      |
| Design indexed record     |        260 | Body progenitor; reflected operation identity is 301   |
| Design operation identity |        301 | Body generic-tag text and face/edge group references   |
| Design indexed record     |        235 | Editable extrusion feature                             |
| Sketch curve identity     | `(102, 0)` | Bottom-circle coedge source link                       |
| ASM state identities      |    4 and 2 | Current and initial journal states in the 7 mm control |

The distinction between operation identity 301 and Design body record 261 is essential. Replacing the generic body tag with the body's indexed record number would change its identity semantics even though both are integers.

The body generic-tag group also contains the integer 4 after its operation-ID text. The historical input calls this `body_generation_reference`. Earlier binary inspection named it the signed secondary ID, independent of stream state IDs; that name is not confirmed by a black-box experiment. Native lineage observations show that it stays 4 after the current kernel state changes to 6 or 7. The same-source experiment supplies it explicitly; current production names it `SecondaryId`.

The native entity stream additionally gives body 261 persistent UUID `ae4be75b-1a15-45aa-bd72-b7bbffe57f6b`. That UUID remains in the enclosing Design document; it is not inserted into a kernel field that does not store it.

## Native lineage observations

| Native archive         | Current state | Initial state | Body key | Next entity tag | Body generic secondary ID |
| ---------------------- | ------------: | ------------: | -------: | --------------: | ------------------------: |
| `extrude_07mm.f3d`     |             4 |             2 |        0 |               1 |                         4 |
| `extrude_13mm.f3d`     |             6 |             2 |        1 |               2 |                         4 |
| `vendor_23mm.f3d`      |             7 |             2 |        1 |               2 |                         4 |
| `vendor_graph23mm.f3d` |             7 |             2 |        1 |               2 |                         4 |

In these controls, the first two preamble integers happen to equal the current state ID. Earlier binary inspection read them as distinct current and maximum allocated state IDs, and the fourth value as the next entity tag. Those readings are not confirmed by a black-box experiment. The corrected generator accepts explicit `stream_current_state_id`, `max_state_id`, `next_entity_tag` and `board_status` inputs. Its loader accepts the old `stream_generation`, `allocation_counter` and `board_number` spellings only to reproduce the unchanged historical input artifact; conflicting old/new spellings reject.

The generated 19 mm stream keeps body key 0, current state 4, initial state 2, stream current/maximum state 4 and next entity tag 1. This preserves the original archive's same-source linkage profile while replacing its solved geometry. A native recompute is free to allocate a different body key and stream state IDs afterward.

## Newly allocated record graph

The analytic cylinder remains the independently authored 26-record topology already accepted as standalone SMT and binary ASM. Its first record is `asmheader`; record 1 is the body. The body, lump, shell, faces, loops, coedges, edges, carriers, vertices and point coordinates are built from the semantic cylinder model.

The nine attribute records are appended at new ordinals, unlike the native control's interleaved attribute allocation:

| New record |                 Owner | Attribute                                               |
| ---------: | --------------------: | ------------------------------------------------------- |
|         26 |                Body 1 | Authoring timestamp; next attribute 27                  |
|         27 |                Body 1 | Generic body identity; previous attribute 26            |
|         28 |           Side face 4 | Selector 1, label `3`, operation 301                    |
|         29 |            Top face 5 | Selector 1, label `2`, operation 301                    |
|         30 |         Bottom face 6 | Selector 1, label `1`, operation 301                    |
|         31 |           Top edge 15 | Selector 2, label `-1`, operation 301                   |
|         32 |        Bottom edge 16 | Selector 4, label `-102`, operation 301                 |
|         33 | Bottom side coedge 12 | Sketch identity `(102, 0)`, sense 0, enum pair `(1, 1)` |
|         34 |  Bottom cap coedge 14 | Same explicit sketch identity                           |

Entity attribute heads and both directions of the body attribute chain refer to these new ordinals. Every owner and topology reference belongs to the newly allocated table. No old binary offsets or raw attribute fragments are reused.

The modern attribute prefix is reserved reference `-1`, integer marker `-1`, next reference, previous reference and owner reference. A generic family payload then stores the family name, schema integers `3, 3, -1`, the repeated family name with a trailing space, and a semantic group count.

The body group stores primary byte length 3, operation 301 as decimal text, secondary ID 4, operation count zero and approach ID zero. Face/edge groups store their primary byte length, label text, secondary ID zero, operation count, operation identity integers and approach ID zero. Historical artifacts retain the old selector/generation names; the later corpus evidence supersedes that interpretation. Labels `-1` and `-102` are text, not null pointers.

The sketch payload stores schema markers 1 and 1, payload form 3, and an ASCII six-integer tuple. Its fourth tuple member is the zero-qualified topology role flags, not an inserted separator. The other fields are primary ID, secondary ID, direction and one-based split sequence/total, as established by the later [ASCII serializer evidence](../EntityGraph/SketchAsciiSemantics.md). The authoring timestamp is an explicit floating-point Unix-microsecond input, distinct from the file save date.

## Complete new insertion journal

The header is `ASM BinaryFile8` plus words `23200, 0, 2, 3`. Word 2 denotes the two top-level roots including `asmheader`, not a record-table offset rule. The product/version/save strings are explicit `Kit` provenance. Binary scale metadata is explicitly 50 to match the enclosing history profile; geometric lengths still serialize in centimetres.

The history preamble contains the explicit fields the generator calls current and maximum state IDs, retained-state limit (zero) and next entity tag, and the bounded two-node reference profile `-1, 0, 1, -1`. Its record begins with `Begin-of-ASM-History-Data` followed immediately by a second identifier, `history_stream`.

The current delta state has ID 4 and node index 0, with previous node `-1` and next node 1. Backward flag 1, a zero-qualified boolean, a self-linked partner ring, a null-qualified state reference, owner-stream reference 0 and absent optional name form the observed two-node profile. One board with owner 0 and succeeded status 2 inserts every newly allocated active record 1 through 34. Each insertion is encoded as a presence integer, old reference `-1` and new table ordinal.

The change-chain zero, board-chain zero and zero count for the state list close the current state. The general semantic purpose of that list remains unresolved; the two-state profile qualifies it empty. The initial delta state has ID 2, node index 1, previous node 0 and next node `-1`; its board chain is empty. There are no archived revisions because this journal describes new entity insertion only.

The stream ends with the two consecutive name chains `End-of-ASM-History-Section` and `End-of-ASM-data`, without an intervening record delimiter or final terminator. This is the fully observed empty archived-revision form.

Research framing accounts for all 5,286 emitted bytes, recovers 35 active records and two history nodes, and verifies that all initial references are in range. Reversing the 34 insertions leaves the initial `asmheader` singleton. These are structural observations; native acceptance is recorded separately.

## Geometry and separate Design caches

The generated solid has radius 1 cm and height 1.9 cm, with base center `(0, 0, 0)`. Expected volume is `5.969026041820607` cm³, center of mass `(0, 0, 0.95)` cm and bounding box `(-1, -1, 0)` to `(1, 1, 1.9)` cm. The expected surface area is `18.2212373908208` cm².

The enclosing Design body record 261 has its own saved cache with volume, area, centroid, inertia, error estimates and revision GUID. The OGS display geometry is another separate saved representation. This generator does not modify either cache. In the accepted same-source experiment, no explicit mass-cache patch was necessary: native initial volume and bounding height reflected the generated 19 mm BRep, despite the retained earlier cache fields. Automatic cache invalidation or recomputation is an inference from those observations, not a traced internal mechanism. This one result does not establish a universal rule for every saved cache or geometry operation.

The native 7 mm cache's inertia about X is approximately `0.908967`, which agrees with unit-density inertia about the origin, not the centroid. `CacheMeasurements.json` records both reference frames for the new cylinder. The origin-frame values are approximately `(8.674984514112616, 8.674984514112616, 2.9845130209103035)` cm⁵; centroid-frame values are approximately `(3.2879385113695174, 3.2879385113695174, 2.9845130209103035)` cm⁵. Error estimates and revision invalidation semantics remain separate research questions.

## Reproduction

```sh
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepHistory/GenerateHistory.py re/Fusion/Reconstruction/BrepHistory/CylinderNineteen.json re/Fusion/Reconstruction/BrepHistory/IndependentNineteen.smbh
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepTokens.py re/Fusion/Reconstruction/BrepHistory/IndependentNineteen.smbh re/Fusion/Reconstruction/BrepHistory/IndependentNineteen.tokens.json
uv run --python 3.14 --no-project python re/Fusion/Reconstruction/BrepModel.py re/Fusion/Reconstruction/BrepHistory/IndependentNineteen.tokens.json re/Fusion/Reconstruction/BrepHistory/IndependentNineteen.semantic.json
```

No test suite or CAD runtime participates in generation or framing. Native import, initial measurements, later feature edit/rebuild, save and reopen are performed only by the parent-controlled oracle workflow.

## Native acceptance

The [archive rewrite provenance](../../LocalOracle/Features/CacheRewrite.json) binds generated geometry SHA-256 `077ab663e22ea712f58c9745466c2035bd62ba496933da84668a708fa2d347c2` to enclosing archive SHA-256 `150b3d2f2eee8c8e81bbd8f5adab1294138260af3938a9fb808555f7924af86b`. The parent reconstructed all 289 Design records from typed fields and replaced the solved BRep member with this independent stream. Other source archive members were retained.

The [native acceptance report](../../LocalOracle/Features/CacheAcceptance.json), from Fusion 2706.1.17, reports:

| Stage                              |         Height, cm |       Volume, cm³ | Topology                     | Driving expression |
| ---------------------------------- | -----------------: | ----------------: | ---------------------------- | ------------------ |
| Initial open before `computeAll()` |                1.9 | 5.969026041820864 | 3 faces, 2 edges, 2 vertices | `19 mm`            |
| Explicit rebuild                   | 1.9000000000000001 | 5.969026041820864 | Same                         | `19 mm`            |
| Native edit and rebuild            | 2.3000000000000003 | 7.225663103256217 | Same                         | `23 mm`            |
| Native save and reopen             | 2.3000000000000003 | 7.225663103256217 | Same                         | `23 mm`            |

The timeline retains sketch `Radius10mm` and editable extrusion `Kit ControlledExtrusion`. Parameter `depthLength` drives the extrusion's dependent `d2`; `d3` remains a zero-degree taper. The saved 23 mm archive has SHA-256 `34ffd05771e10959c526ca1a8cf9652964ee575b87ebbb67ff482517f4dda4b4`. The report records zero remaining documents after cleanup.

The initial 19 mm height is the important new observation: the model no longer waits for a native rebuild to reconcile the parameter edit with stale saved geometry. The native report measures volume, height and topology; it does not record centroid or inertia for this embedded-cache experiment, so the analytic values above remain expectations for those additional quantities.
