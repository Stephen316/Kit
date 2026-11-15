# P04 sketch records in the configuration stream

## Evidence

The remote discovery census for PR head `6cec3b3a7d2bc71413abb62f94255fb1d96d3ad2` ran on checkout `dc3c652d472eabe4620dce6bb7a16e8d95c92c42`. Census JSON SHA-256 is `897912d6c8d9898b57a3820ac9c8ab0cecb64684cb20db5aa23e8efdeaddbfbc`. Both P04 baseline A sketches have zero parsed markers. Their resolved-stream spans are 5,549–6,399 for `RectangleSketch` and 9,419–13,007 for `CutSketch`.

Read-only container inventory used [P04 baseline A](../../automation/PairedCaptures/P04/solidworks-c1986308375a/P04-solidworks-baseline-a.SLDPRT), Git blob `a195dde7efc466d8660e083a4e191bfef32bd1ce`, SHA-256 `c1986308375aaf68ebac6f8de61e70a47b9b33535c94271bab2e4bd00504c59d`. The input identity and application evidence are in the [capture receipt](../../automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json). No CAD process, reader test or P05 inputs were used in this inventory.

## Observations

- The 16,256-byte `Contents/Config-0-ResolvedFeatures` stream contains one `ff ff 1f 00 03` marker at 4,840, before both measured sketch spans. Neither span contains an accepted marker prefix. The existing sketch decode reads only the resolved feature span.
- The 42,879-byte `Contents/Config-0` stream has 20 of the existing 2026 marker prefix and SHA-256 `e40cdd1e562a9e501a0a29ac252745d5c5cac6a7265ef924ccef4f5d078b34ab`. Its two ten-marker groups begin at 3,800 and 12,937. The first follows an `sgSketch` class definition at 3,772. The second follows a reference to the same class at 12,921. Each sketch begins with a point count of 5.
- Using the established point tag at marker +56 or +64 and two little-endian doubles in metres, the first group's rectangle corners are `(15,6)`–`(25,14)` mm in XY. The second group's corners are `(0,0)`–`(40,20)` mm. On the width-44 edit, the groups move to `(17,6)`–`(27,14)` and `(0,0)`–`(44,20)` mm. On the cut-width-12 edit, the first reaches `(14,6)`–`(26,14)` while the second stays unchanged. On YZ both groups use their native local coordinates `(-Z,+Y)`. The local marker indices repeat across groups.
- Name-framed dimension scalar records immediately following the first group carry IDs 36, 37, 39 and 40 for `cut_width_mm`, `cut_height_mm`, `cut_left_mm`, and `cut_bottom_mm`. The second group precedes IDs 27 and 28 for `width_mm` and `height_mm`. IDs and names remain stable after reopen and across the tested shape and plane edits. The KeyWords XML explicitly lists these dimension names under feature 35 `CutSketch` and feature 26 `RectangleSketch`, respectively. The XML does not carry the observed dimension scalar IDs.

## Cross-stream sketch ownership

The follow-up inventory checked all eleven P04 captures at Git revision `466dcb172dfa3803463e07ccde963ba01671d200`. The committed receipt SHA-256 is `7fd2fffa3c690998753a80cab81da2f1c2446c9fcec39574e3983a7f4345cae5`. Each file matched its recorded SHA-256. The two feature records contain object references to their sketches in the earlier configuration stream. Both streams use the same class and object index space. [Cross-stream map evidence](../archive/ExternalClasses.md#2-the-index-is-not-a-fixed-number-and-not-a-function-of-base)

| Baseline A feature | Feature tree ID | Resolved stream reference offset and bytes | Config-0 object start | First geometry marker |
| --- | --- | --- | --- | --- |
| `RectangleSketch` | 26 | 5,742, `9b 00` (object 155) | 12,921 | 12,937 |
| `CutSketch` | 35 | 9,600, `4a 00` (object 74) | 3,772 | 3,800 |

The resolved reference is the sixth direct child of `moProfileFeature_c::Serialize` (layout slot 5). The traced baseline records this child as `sgSketch` at node 156. The traced vendor ring records an `sgSketch` with object index 304 at node 436, then shows two `moSkDimHandleValG2_c` dimension handles reading backreferences to object 304 at nodes 728 and 757. These traces identify the archive operations and their expected target class. The P04 captures use backreferences at the resolved profile slot. [Profile layout](../../data/Layouts/ClassLayoutsDecompiled.json), [baseline trace](../../data/segments/Streams/SegmentsBaseline.json), [dimension handle trace](../../data/segments/Streams/SegmentsVendorRing.json)

In baseline A, the `cut_left_mm` relation's first dimension handle body begins at 3,662. At body +110 it opens a new `sgSketch` class and object. The `width_mm` relation-side wrapper has value `0.040 m` and its handle body begins at 12,811. Its sketch child at body +110 begins with `49 80`, which is the class-reference token for class index 73. A class definition allocates a class index followed by an object index, so the first sketch has object index 74. The second handle creates another object of that class. The nested dimension records inside that second sketch refer back to object 155, at 15,798 and 17,241. The corresponding records inside the first sketch refer back to object 74, at 7,125, 8,590, 10,033 and 11,476. The two groups have independent local dimension indices starting from zero. [Archive tag and allocation rules](../archive/Segmentation.md#3-the-map-counter--increment-rule-as-observed)

Later equation handles cross-check both owners. Baseline A's cut width, bottom and height handles use object 74 at 18,565, 19,293 and 19,965. The parent height handle uses object 155 at 19,673. Across the edited saves the parent width wrapper changes from 40 to 44 mm, the cut width wrapper from 10 to 12 mm, the parent height wrapper from 20 to 24 mm and the cut height wrapper from 8 to 10 mm. Both profile references persist through these edits, repeat save, YZ, inch display and through-all termination.

| Variant group | Rectangle reference | Cut reference | First and second Config-0 object starts |
| --- | ---: | ---: | --- |
| Baseline A | 5,742 | 9,600 | 3,772 and 12,921 |
| Baseline B, six parameter edits and inch display | 5,742 | 9,828 | 3,810 and 12,959 |
| YZ | 5,742 | 9,670 | 3,770 and 12,919 |
| Through-all | 5,742 | 9,598 | 3,770 and 12,919 |

## Reproduce the inventory

1. Read each of the eleven files as bytes from Git at the recorded revision and verify it against the capture receipt. Open the container with `SldprtArchive.from_bytes` and extract `Contents/Config-0` and `Contents/Config-0-ResolvedFeatures`. [Container reader](../../../src/convert/adapters/solidworks/container/Container.py)
2. In the resolved stream, locate each feature name in its framed UTF-16 `moNodeName_c` record. The feature tree ID is the little-endian integer at name end +8. In these eleven files, the sketch child begins at name end +157. Read its little-endian object tag and compare with the offsets above.
3. In `Config-0`, identify the `moRelDimension_c` → `moDimRefWrapper_c` → `moSkDimHandleValG2_c` chain. For baseline A the cut-left wrapper scalar starts at 3,628 and the parent width wrapper scalar at 12,801. At each handle body +110, inspect the class tag or backreference. Cross-check the two object IDs against the interior dimension handles and against the resolved profile slots.

Only the recognized sketch child slot establishes ownership. The same resolved records contain `4a 00` in the middle of four-byte fields at name end +50 and +58. A token search would find these unrelated hits in both sketches. Marker order is also reversed relative to the feature tree.

## Remaining integration

The cross-stream link is established for these P04 discovery files. Production decoding needs a versioned walk of the profile sketch slot and the shared archive object map. Trace or parse object allocations to identify each `sgSketch` span, including inline objects and class references. Preserve geometry and dimension provenance in `Config-0` and owner-reference provenance in `ResolvedFeatures`. The observed fixture offsets and object indices can serve as regression evidence.

The matching loader confirms the map handoff to the resolved-feature read. Licensed baseline A and YZ traces identify the unit component's first reference as the loaded part at slot 2. The strict walk from that map seed reaches the first `sgSketch` allocation at class 73 and object 74 in all eleven captures. It follows the first equation's dimension handle to the sketch pointer. The older sketch layout's terminal guard stops inside the first sketch after the entity-handle and external-reference continuation. [Archive map and loader walk](P04ArchiveWalk.md), [atom and first sketch walk](P04AtomWalk.md)

The resolved stream identifies `CutSketch` as face-supported. [Licensed native readback](../../../Documentation/Changes/Research/Workers/SolidWorksCutFaceReadback.md) independently identifies the same persistent boss-face support before and after rebuild in all eleven files and records the support transforms. The [typed archive replay](../../../Documentation/Changes/Research/Readers/SolidWorksFaceOccurrence.md) reaches that occurrence from the cut profile in both traced controls.

## Licensed sketch boundaries and resolved references

Four separate SOLIDWORKS `34.4.1.1011` sessions read the pinned P04 baseline A and YZ captures. Two sessions traced sketch serializer entry and exit. Two traced the subsequent resolved-feature sketch reads. Each compared the complete runtime archive buffer with the decompressed capture SHA-256. The cross-stream sessions verified both full buffers. All scratch part hashes stayed unchanged after the owned processes exited. [Capture and executable pins](P04ArchiveWalk.md#inputs)

The `sgSketch::Serialize` entry at `sldmodu+0x144f790` receives the sketch and archive in `rcx` and `rdx`. The matching exit at `0x1457e80` uses `rsi` and `r14`. At entry, the archive counter minus one selects the slot whose value equals the receiving sketch pointer. The exit observation pairs the same sketch, archive and buffer and records the final cursor and allocation counter. Both entries use generation 19000, context mask zero and the load branch with an empty embedded profile field.

| Capture | Resolved feature | Config-0 object slot | Config-0 body and end | Allocation counter | ResolvedFeatures reference |
| --- | --- | ---: | --- | --- | ---: |
| Baseline A | `CutSketch` | 74 | 3,786–12,532 | 75–147 | 9,600 |
| Baseline A | `RectangleSketch` | 155 | 12,923–18,277 | 156–200 | 5,742 |
| YZ | `CutSketch` | 74 | 3,784–12,530 | 75–147 | 9,670 |
| YZ | `RectangleSketch` | 155 | 12,921–18,275 | 156–200 | 5,742 |

The profile serializer's typed `sgSketch` pointer read at `0x9dbbcf` receives the later archive. The two-byte token selects the same sketch pointer observed in the Config-0 allocation. Immediately after the call at `0x9dbbd4`, the profile member at `[[rdi+0x3d0]+0x80]` contains that exact pointer. Each read consumes two bytes and leaves the allocation counter unchanged. The observed IDs and offsets are regression evidence for a versioned archive walk.

## Native map handoff

Three further owned sessions followed the archive from the [relation manager return](P04SketchGap.md#follow-the-second-sketch-return) through the final Config-0 cursor. The model cache copies the active array at `sldmodu+0xece7ef`. Before `ResolvedFeatures` reads its first list at `0x4489de`, the archive has consumed its four-byte header and restored the same allocation counter and the same two sketch instances. Both full runtime buffers matched the pinned stream hashes in each session. Each scratch part kept its original hash after the owned process exited.

| Capture | Config-0 reads after relation manager | Cursor at cache | Next map index at cache and before resolved list |
| --- | ---: | ---: | ---: |
| Baseline A | 94 | 42,879 | 279 |
| YZ | 96 | 42,949 | 279 |
| Width edit, 44 mm | 93 | 42,925 | 279 |

The private normalized map-handoff witness SHA-256 is `54f90a4fa10312c19bab9422e6a493daa96034187083b4a02203e087080c5bb9` for baseline A, `fd422752ee69e812b6cfc43c18ca2392f859c388a24b429b0ab41ed14d780423` for YZ, and `959afea685896f886a1340edf7394b81fce1f83e65b69d22820b577cbece6dda` for the width edit. In each trace, calls with the same cursor, counter, and token reduce to 92 distinct pointer reads.

### Offline map replay

`python re/solidworks/archive/ConfigMap.py` reconstructs the complete typed `Config-0` map for all eleven receipt-pinned P04 discovery captures. It starts with the actual sketch and relation manager allocations, walks the presentation suffix, and hands back the map at stream end. It compares the counter to the resolved header after completing the walk. All eleven produce counter 279 and retain sketches at slots 74 and 155. All 92 cursor, counter, and raw tag observations match each of the three licensed traces. The report SHA-256 is `d54ce30559d5905d56c290f4dabb3e961861673afeccc3071dc7cac40202853a`. A changed schema on the sole schema-zero declaration, `moFeatColorTab_c`, is rejected in each traced capture.

The first annotation view stores a framed name and two `mgXform` values. The reader follows `moView_c::Serialize` at `sldmodu+0x10ea1d0` into the two `mgXform::restore` calls. Each transform has a matrix flag, nine additional doubles when set, four doubles, and a reference flag. The YZ `*Right` view has the 72-byte matrix that the baseline `*Front` view omits. The tagged continuation also follows the second `*Top` view.

Two licensed field traces resolve the eight-byte difference after the bend-note pointer. Both read an empty text-pair table and traverse the 13-byte scalar run to the inline sketch-region count at `sldmodu+0x10f5514`. Baseline A has one populated `moSketchRegion_c`. The width edit adds an empty region before its populated region and stores another four-byte value after both regions. The region loader at `0xadce00` reads a row count and two integers plus one double per row. In baseline A the count is at 42,366 and the exploded-view pointer at 42,648. In the width edit they are at 42,404 and 42,694. The private field summaries are `677a2bd7311bbd18b1a7a957c5e251ef41e6927c80cb200d8facdfaeabd42c7f` and `f35eeb09e8395cbe7a5ef221044d57c22a66bc592b25f22b241d977277b0d2e8`, respectively. Seven captures use two regions, covering the six parameter edits and the inch variant. The two baselines, YZ, and through-all use one region.

This map replay is scoped to the eleven P04 discovery archives and the witnessed application build. The fixed presentation spans preserve their typed boundary checks. Their internal fields and the full subsequent resolved-feature list still need to be decoded before production qualification.

## Face reference control

In every measured P04 `Config-0-ResolvedFeatures` stream the class name `moFaceRef_c` appears once. A 52-byte interval beginning 25 bytes after the first byte of that name is also present at the same relative location in the support face's private persistent reference, before and after rebuild. This interval crosses the `moEndFaceSurfIdRep_c` declaration. The first byte of the archived class name is 6,652 in baseline A, 6,880 in baseline B and the parameter and inch variants, 6,722 in YZ and 6,650 in through-all.

The licensed collector verified that the boss's five other faces in each observation resolved to their own distinct objects. The opposite cap shares the same interval in all 22 observations. The four side faces do not share it. The span identifies a cap-family candidate. Resolving the cut sketch's specific reference requires the enclosing typed object reference and an independently verified occurrence discriminator. The collector preserves both cap references with their native normals in the private measurement report.

## Licensed cut-sketch support owner

Two additional owned `34.4.1.1011` sessions bound the support read to the profile that received the `CutSketch` configuration object. The `sgSketch` pointer result at `sldmodu+0x9dbbd4` supplies the profile, archive and exact sketch identity. In that same profile, the call at `0x9dbdc6` reads a support object with selector `1`. Its token `0x8152` selects the live class map entry `moCompRefPlane_c`. The result at `0x9dbdcc` becomes the effective profile support at `0x9dc16a`. The earlier candidate support pointer was empty in both sessions.

| Capture | Support token position | Support object end | Profile continuation | Next map index before and after |
| --- | ---: | ---: | ---: | --- |
| Baseline A | 11,531 | 12,588 | 12,658 | 456–475 |
| YZ | 11,595 | 12,724 | 12,866 | 456–475 |

These positions are relative to the full `ResolvedFeatures` stream. At the support read, the native archive has refilled the buffer and its cursor is buffer-relative. Each session matched a unique 64-byte window ending at the support return to the pinned full stream, then verified the 64-byte window at the resulting support start. Both collectors exited and rechecked the original part hashes. The private normalized witness SHA-256 values are `e3be0391bc0f73aa2683ebcedb393369728314ea9ee2bc14d84a39d589597a38` for baseline A and `8e8207076ceaee731d6c9ed79016e32ebe622a67a8788ade87206ca4a91c7e48` for YZ.

Follow-up licensed traces resolve the support geometry through live class 320 `moRefPlane_c`. Its nested `moFaceRefPlnData_c` allocation is slot 460, and that object's `moCompFace_c` allocation is slot 462. Both serializer entries match their live map entries and native vtables. At `sldmodu+0xa63e98`, the component reads token `0x8174`, creating an object of the existing `moFaceRef_c` class declared earlier in the stream. At `0xa63e9e` the result matches only live object slot 464 and the `moFaceRef_c` vtable. Both reads advance the map counter from 464 to 475.

| Capture | Face-plane data body | Component-face body | Face-reference token and return |
| --- | ---: | ---: | ---: |
| Baseline A | 11,951 | 12,114 | 12,200–12,366 |
| YZ | 12,015 | 12,250 | 12,336–12,502 |

All four additional sessions opened the pinned part read-only, exited through the owned session and confirmed the source hash. The normalized nested-entry witnesses have SHA-256 `483a9fad8198dc2714b081943f828d41e8da3f09719547e8f6fe2a33d04a6717` and `3b172b14aa63a4f6e418feaff0f1eac14fb66bac198a53ded91a1b24db5d4f25`. The exact component-face pointer witnesses have SHA-256 `a9c3f9f144e65428a69c6e283224ee5dd3f2e9da12035e217519fd377bbde051` and `65e3d015dbb7505ccce2464c3f7b3b007d86a8eb3cd514d6f83cff2e39644da6`, respectively.

## Supporting-face occurrence control

The typed `moFaceRef_c` body begins two bytes after the component-face token. In this observed layout, the primary end-face representation carries a three-dword tuple at body +46. It records the boss feature ID, native archive time and face occurrence. Four ordered boundary surface representations carry further tuples at body +70, +90, +110 and +130. The independent persistent references declare the first boundary type inline, which shifts their later tuple offsets.

All eleven pinned P04 discovery archives matched the primary and four ordered boundary tuples in the independently reopened support face both before and after rebuild. Every opposite cap matched the primary feature and time but had occurrence `0` where the supporting cap had occurrence `1`. The other four boss faces in each observation had a different primary representation type. The sweep covers 22 positive face observations and 110 distinct boss-face controls. Its private normalized summary SHA-256 is `a2d342b1c27cee0edab45494d116c8debf7eeca1f51bc8101da4dfe97be0f203`. The supporting-face fields can now be compared independently in this discovery set. Production still needs the typed structural walk from the resolved profile through its support and face reference. [Licensed persistent references](../../../Documentation/Changes/Research/Workers/SolidWorksCutFaceReadback.md)
