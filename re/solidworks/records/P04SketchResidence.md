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

The matching loader confirms the map handoff to the resolved-feature read. A guarded configuration walk reaches the unit-component record in all eleven captures and stops at its first reference to incoming object slot 2. [Archive map and loader walk](P04ArchiveWalk.md)

The resolved stream identifies `CutSketch` as face-supported. [Licensed native readback](../../../Documentation/Changes/Research/Workers/SolidWorksCutFaceReadback.md) independently identifies the same persistent boss-face support before and after rebuild in all eleven files and records the support transforms. Mapping that face occurrence to its archive encoding remains open.

## Face reference control

In every measured P04 `Config-0-ResolvedFeatures` stream the class name `moFaceRef_c` appears once. A 52-byte interval beginning 25 bytes after the first byte of that name is also present at the same relative location in the support face's private persistent reference, before and after rebuild. This interval crosses the `moEndFaceSurfIdRep_c` declaration. The first byte of the archived class name is 6,652 in baseline A, 6,880 in baseline B and the parameter and inch variants, 6,722 in YZ and 6,650 in through-all.

The licensed collector verified that the boss's five other faces in each observation resolved to their own distinct objects. The opposite cap shares the same interval in all 22 observations. The four side faces do not share it. The span identifies a cap-family candidate. Resolving the cut sketch's specific reference requires the enclosing typed object reference and an independently verified occurrence discriminator. The collector preserves both cap references with their native normals in the private measurement report.
