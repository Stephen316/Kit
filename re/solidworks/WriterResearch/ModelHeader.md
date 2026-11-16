<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A12 generation-19000 ModelHeader

The spatial frame and archive allocation rules below cover the saved **P01, P03 and P04 discovery files**. The immediate writer target is the single rectangular blind boss in P03. A complete source-independent ModelHeader remains unverified. Two streams had identical decompressed bytes in all 25 captures: `Contents/Config-0-ModelHeader` and `Header2`.

## Evidence

The corpus inspection used PR #94 checkpoint `08f2f8e6514ca1dfcf8a2dba98845d1c53430af1`. It verified each native file SHA-256 and each measurement receipt digest before reading the header. Every container carried `_MO_VERSION_19000`. P05 remained reserved.

| Discovery controls                                                                                 | Files | Receipt SHA-256                                                    | Baseline A header SHA-256                                          |
| -------------------------------------------------------------------------------------------------- | ----: | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| [P01 rectangle](../../automation/PairedCaptures/P01/solidworks-75b9308cf13e/receipt.json)          |     6 | `3c389fe4069bece7ecf64f0294d111ce7f44131b2fc576d3f2ac4291e0fec7bf` | `33e489a050a6bfee29a85795a287187b865036bffdecbc1ac7ff1f126dfb67db` |
| [P03 blind boss](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)         |     8 | `f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94` | `ca9903271fec44cad545934a7b2250fa3ed5e34511346320ca185b134973812c` |
| [P04 face-supported cut](../../automation/PairedCaptures/P04/solidworks-c1986308375a/receipt.json) |    11 | `7fd2fffa3c690998753a80cab81da2f1c2446c9fcec39574e3983a7f4345cae5` | `c9d70fffb78b8cb14a70a395337f93d2e59143e9d87f005fd025bbb58053407f` |

The compact UTF-8 JSON list of `[native filename, decompressed Header2 SHA-256, byte length]` in receipt order (P01, P03, P04) has SHA-256 `dc25d05921a1cbb6c7cd3afcb0e4014aafaa554f048b6fdf3241935a0cacad4d`. The existing measurements provide independent world sketch endpoints, support identities, boss depth and direction. No additional application run was required for this corpus inspection. [Licensed SOLIDWORKS discovery readback](../../../Documentation/Changes/Research/Workers/SolidWorksQueuedReadback.md)

## Archive and object rules

- **Confirmed layout.** `Native.ReadHeaderRoot` reaches the document log list in all 25 files. The root archive context is 1, its first two children are string arrays, and the third is the counted `suObList`. The list has one document log, 23 document-default logs, then the actual authored object logs. Counts are 25 for P01, 26 for P03 and 28 for P04. Each authored log has its allocated native history ID and name. The normal P03 aliases are the `RectangleSketch` and `BlindBoss` nodes. Use the same allocated IDs throughout the generated document. [PR reader](../../../src/convert/adapters/solidworks/Core/Native.py), [archive segmentation and growth](../archive/Multistream.md#contentsconfig-0-modelheader-and-header2--156-bytes-5-objects-per-feature)
- **Refuted ordinal rule.** `Native.ReadHeaderObjs` accepts 11 files and rejects all 14 edit and inch files with an action-index error. Read the stamp body as little-endian `<3HI` followed by its counted string. The first u16 is observed as 0 for `Created` and 1 for every `Modified`. Repeated edits append another 1, even after the second action. The next two u16s are zero in this scope. Fresh P03 documents already log `Created` and `Modified` for both the sketch and boss, unlike the older one-action boss examples.
- **Confirmed allocation.** After the final authored log, read `<IIHI` for the archive time, next-ID state, null external-list reference and update stamp, then read the explicit self `moExtObject_c`. The self object owns a document path handle and a second handle that references the same `moCStringHandle_c` class. Its class index equals `14 + sum(1 + len(actions) for each non-root log)` across all 25 files. The sum expresses archive allocation on every log and stamp. Generate this class index from the emitter's allocation map. A P03 baseline has class index 71, while the inch variant has 76. Some document reference names differ between the initial log and the self object. Use distinct input roles for the creation-time reference and the current self name.
- **Refuted watermark shortcut.** Taking the greatest header log ID plus one gives 35 and 47 in P03 and P04, but predicts 27 for P01. The actual next-ID state is 29 in all six P01 files. Header logs are an incomplete list of allocated feature and related IDs. The writer needs to allocate the complete document graph before deciding this state field.

The typed [self-reference reader](HeaderSelf.py) follows the live map through the external object and its two CString handles. It reaches byte 2,141 in the 2,359-byte P03 baseline, with next archive index 74, and byte 2,529 in the 2,747-byte inch variant, with next index 79. Both positions leave 218 bytes. The self object shares the file path, title, shared file time and configuration name with CMgr. Its saved flag is 8 in both path forms, and it has a separate last-modification time. [Shared file fields and their native store sites](CmgrTail.md#external-file-and-referenced-configuration)

## Revision log construction

Installed SOLIDWORKS `34.4.1.1011` uses `sldarchiveu.dll` with SHA-256 `fce17ce9f2b79e188ee0c20ca51cd36cd246d92bf2d35c2010a03f4bb5c304c6`. The `moHeader_c`, `moLogs_c` and `moStamp_c` virtual archive entries are `0x31a134f0`, `0x31a14830` and `0x31a148b0`, respectively. The [typed constructor](HeaderLogs.py) starts the ordinary archive map at slot 1 and continues through the fields immediately before `moExtObject_c`.

| Record | Native store evidence |
| --- | --- |
| Root opening | `0x31a13575..86` writes the archive context flag. The calls at `0x31a13593` and `0x31a135a0` write the two string array pointers. `0x31a13626` writes the log list. |
| Log members | `0x31a14845` writes the inline counted stamp list. `0x31a1485e` saves the tree ID from member `+0x48`, and `0x31a1487a` writes the name at `+0x50`. |
| Stamp members | `0x31a148dd`, `0x31a148ea` and `0x31a148f7` store the low words of `+0x08`, `+0x0c` and `+0x10`. `0x31a1490e` saves the timestamp at `+0x18` and the return branch writes the CString at `+0x20`. The constructor at `0x31a12790` receives the status enum independently, and the exported `updateStamp` at `0x31a163e0` stores a new status and current time. |
| Root continuation | `0x31a13665` stores the time from header `+0x50`. It agrees with the root document log creation time in the pinned profile. The standalone creation-time getter at `0x31a15160` refers separately to `+0x70`. `0x31a13671` saves next tree ID from `+0x08`, and `getHighestID` returns that member minus one at `0x31a15230`. The external list pointer at `0x31a1367e` is null. `0x31a136b3` saves the update stamp from `+0x40`, corroborated by its getter at `0x31a09810`. |

The six P01, eight P03 and eleven P04 saved headers have 25, 26 and 28 logs respectively. All 666 logs begin with status 0 for creation. Their later 248 stamps use status 1, including repeated modifications in one log. The file log uses ID 0. The 23 default feature IDs occur in the fixed saved order `1..18,21..25`. Their names agree as a multiset with the independent native feature tree, which uses display order. All authored log names agree in order with that tree. The next ID remains an explicit input because other native objects can consume IDs without creating header logs. [Pinned replay and hosted comparison](../../../Documentation/Changes/Research/Writers/SolidWorksModelHeaderLogs.md)

## Continuation and spatial frame

Let **C** be the byte immediately after the self record's counted configuration-name string. The stream has 234 bytes from **C** in all 25 controls. The snapshot decodes the first 16 as the self-reference's configuration ID and three additional 32-bit fields, with little-endian layout `<iiIi`. All four are zero in the controls. The following offsets are relative to **C**.

| Offset | Width | Evidence and writer implication                                                                                                                                                                                                                                                                                                                                                                                     |
| ------ | ----: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| +16    |     4 | Current body stamp from `moHeader_c+0x44`, written at `0x31a1371f` and exposed by `getCurrentBodyStamp` at `0x31a08a10`. It is 105 in fresh P03 Front, Right and reverse controls and varies through 121 over other P03 saves. |
| +28    |     4 | Creation time from `moHeader_c+0x70`, written at `0x31a13818` and exposed by `getCreationTime` at `0x31a15160`. It matches the self object's shared file time in these controls. |
| +50    |     4 | License flag from `moHeader_c+0x7c`. `0x31a13973` saves it and `getLicenseFlag` at `0x31a152a0` reads the same member. All 25 measured values are 4. |
| +54    |     4 | Current update time from `moHeader_c+0x48`, written at `0x31a139b2` and exposed by `getCurrentUpdateTimeStamp` at `0x31a08a60`. The P03 baseline differs by one second from the earlier self-reference modification time, which comes from `moExtObject_c+0x60`. |
| +58    |     2 | Compact `suObList` class reference at archive class index 6 in this branch.                                                                                                                                                                                                                                                                                                                                         |
| +70    |     4 | Bounding-box presence from the pointer at `moHeader_c+0x90`. The serializer writes the presence and inline `mgBBox_c` through `0x31a13a9d..0x31a13aad`. The pointer is present in all controls. |
| +74    |    80 | Ten little-endian f64 values in metres: midpoint xyz, maximum xyz, minimum xyz, then radius.                                                                                                                                                                                                                                                                                                                        |
| +154   |    80 | Three signed words of `-1`, the license type, active content fields, 3DEXPERIENCE icon override, external-reference flags, visible-sketch state, two feature flags and the terminal field. The sequence consumes no archive slot. |

The replaced-components list at +58 reuses the saved `suObList` class and allocates one empty object. The native serializer writes it from `+0x88` at `0x31a139ec`. The preceding null is the linked-attachments array at `+0x28` from `0x31a13904`. Named native setters identify the saved lock, detachable, usage, component-count, copied and freeze fields. The standalone profile has all six clear.

The three signed words after the frame come from the fallback between `+0xd8..0xe0` and `+0xcc..0xd4` at `0x31a13ae7..0x31a13b2c`. The constructor initializes both sets to `-1`. `0x31a13b65` writes the license type from `+0x80`, which `getLicenseType` at `0x31a152b0` also reads. The third signed word and the license type 2 produce the byte sequence previously interpreted as an empty class. Reading the two fields separately preserves the actual allocator.

Six active-content values at `+0x9c..0xb0` and the icon override at `+0xe8` are zero. `syncExtRefFlags` at `0x31a16210` supplies the next five signed values from `+0xf0..0x100`. The saved tuple is `(0,0,0,1,0)`. `updateVisibleSketchFlags` at `0x31a16430` writes `+0x104`, which the serializer saves at `0x31a13ca6`. P01 saves 1 and the other controls save 0. Annotation and graphics-feature setters store the following two zero fields, and `0x31a13d51` writes the final caller state from `+0x98`. The latter is 1 in the measured set and its upstream setter is still unresolved.

The generation-18000 header has different license and trailer values. The older accepted case corroborates the ten-double spatial layout and the dependency between creation-time roles. [Historical header grammar and acceptance](../records/PinRevolutionEnvelope.md#modelheader-closure), [historical modifier ablation](../archive/Multistream.md#terminal-modifiers-also-require-the-model-header-spatial-frame-and-creation-pair)

All 25 generation-19000 saves agree between `ModelStamps` and the header's creation, current update and current body fields. The self object's shared file time also equals the creation field. The self-reference modification time differs from the current update time in 10 files, so the two times need separate inputs. The next tree IDs are 29, 35 and 47 in the P01, P03 and P04 files, while their highest logged IDs are 26, 34 and 46. Tree allocation must account for objects without revision logs.

The bounded calculation uses the world profile endpoints and the endpoints translated by the boss's signed displacement. Use the verified saved plane's positive axis, with the reverse flag applying the sign independently. Minimize and maximize each axis, take the midpoint of those corners, and halve their Euclidean distance for the radius. P01 uses the profile endpoints alone. P04 is a comparison control whose cuts do not extend the outer boss bounds.

All 25 frames agreed with the independently measured geometry within `3.47e-18 m` per value. In P03, the 40 × 20 × 10 mm baseline has bounds `(0,0,0)` to `(0.04,0.02,0.01)` m and radius `0.0229128784747792 m`. The reverse control moves Z bounds to `[-0.01,0]` m. The YZ control extends along **+X**, with bounds `(0,0,0)` to `(0.01,0.04,0.02)` m. Using the third row of the raw measured model-to-sketch transform as the extrusion axis instead predicts **−X** and produces a `0.01 m` bound error in both P03 and P04 YZ controls. [Verified saved extrusion direction](../../../Documentation/Changes/Research/Readers/SolidWorksBlindBossDirection.md)

## Remaining synthesis obligations

The [standalone header constructor](HeaderTail.py) composes the revision logs, self reference and bounding frame on one allocator. It requires distinct caller timestamps, saved flags and license words for the observed profile. A source-independent part still needs to supply those inputs through shared authoring state, build the complete load-critical envelope, and pass independent licensed open, edit, rebuild, save and reopen. [Construction and measured bounds](../../../Documentation/Changes/Research/Writers/SolidWorks/SolidWorksModelHeaderTail.md)
