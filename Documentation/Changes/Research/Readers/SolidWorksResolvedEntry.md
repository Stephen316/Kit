# P04 SOLIDWORKS resolved entry and profile linkage

Run `python re/solidworks/archive/ResolvedEntry.py` from the repository root. The command checks the exact P04 receipt, independent measurements and native file digests. It walks from the resolved list header through the typed opening of BlindBoss's end specification for all eleven captures. For baseline A and YZ it also verifies both decompressed stream hashes and compares the separately witnessed profile links, file reference allocations and CutSketch support cap. The JSON report SHA-256 is `68fad1603a89ea124b4bfd9ef9b4c8f920e4bbd229e1feda48e05b4ab5b3b721`. [Licensed sketch and resolved owner evidence](../../../../re/solidworks/records/P04SketchResidence.md)

The matched native handoff reaches Config-0 byte 42,879 in baseline A and 42,949 in YZ. The resolved list load begins at byte 4 with next archive index 279. The offline reader uses the completed Config-0 class and object map to start the list and to resolve the two separately anchored sketch references. The first four resolved bytes corroborate the counter at 279. The short list count at byte 4 is 21, and the first class definition begins at byte 6. [Offline map replay](../../../../re/solidworks/records/P04SketchResidence.md#offline-map-replay)

| Record | Feature ID | Object slot | Entry | Reached cursor | Next map index |
| --- | ---: | ---: | ---: | ---: | ---: |
| Comments | 8 | 280 | 6 | 203 | 282 |
| Favorites | 23 | 283 | 203 | 410 | 285 |
| History | 24 | 286 | 410 | 606 | 288 |
| Selection Sets | 25 | 289 | 606 | 825 | 291 |
| Sensors | 22 | 292 | 825 | 1,018 | 294 |
| Design Binder | 7 | 295 | 1,018 | 1,221 | 297 |
| Annotations | 1 | 298 | 1,221 | 1,873 | 305 |
| Surface Bodies | 10 | 306 | 1,873 | 2,097 | 308 |
| Solid Bodies | 9 | 309 | 2,097 | 2,315 | 311 |
| Environment alias | — | 240 | 2,315 | 2,317 | 311 |
| Markups | 21 | 312 | 2,317 | 2,513 | 314 |
| Equations | 16 | 315 | 2,513 | 2,707 | 317 |
| Material | 11 | 318 | 2,707 | 2,944 | 320 |

The History variant ends after two guarded folder scalars and the empty history-item count. The short count at byte 604 is the same archive field identified by the historical measured nonempty arrays. The Selection Sets body adds six guarded bytes to the common folder suffix, matching its historical post-comment width. Sensors and Design Binder use the ordinary folder suffix. With the typed name seed applied, the historical generic table places a child at byte 56 inside the Comments node flags in these captures. [History array count](../../../../re/solidworks/archive/Segmentation.md#the-mohistoryfeatitemdata_c-array-count), [node field order](../../../../re/solidworks/records/Feature.md), [historical folder and profile layout](../../../../re/data/Layouts/ClassLayouts.json)

The `moDetailCabinet_c` resolved node list contains two entries. Its first entry allocates Notes at slot 301 and the nested Notes end marker at slot 303. The end marker refers back to Notes. The second list entry refers to the same end marker at slot 303. The reader checks the four-dword trailers of both Notes records. The cabinet then continues through its feature fields and a guarded 32-byte scalar trailer whose field meanings remain open. Its width matches the historical 68-byte post-comment run after accounting for the 36 bytes of common feature fields. [Notes folder trailer layout](../../../../re/solidworks/records/VersionedRuns.md#31-monotesareaftrfolder_c-run-4--16--confirmed)

Both body folders have two null child pointers. The Environment entry at 2,315 is an object reference to the `moEnvFolder_c` already materialized in Config-0. The decoder resolves it against the derived map and leaves the counter unchanged. The last three folders lead to the first schema-1 `moRefPlane_c` declaration at 2,944 with next map index 320. The licensed CutSketch support later references that same class index. [Licensed plane class reference](../../../../re/solidworks/records/P04SketchResidence.md#licensed-cut-sketch-support-owner)

## Principal planes and Origin

Each principal plane uses the shared model-feature and atom fields, reference geometry mode 5, then its typed `moDefaultRefPlnData_c`. The saved plane payload supplies an origin, unit normal and optional local basis. The four typed optional children are empty. The next object tag follows the fourth child directly in both captures. [Default reference plane layout](../../../../re/solidworks/records/VersionedRuns.md#32-modefaultrefplndata_c--confirmed-and-the-one-byte-bug-that-blocked-23-donors)

| Plane | Object slot | Entry | Return | Next map index | World normal |
| --- | ---: | ---: | ---: | ---: | --- |
| Front | 321 | 2,944 | 3,483 | 325 | +Z |
| Top | 325 | 3,483 | 4,049 | 328 | +Y |
| Right | 328 | 4,049 | 4,619 | 331 | +X |

The typed `moOriginProfileFeature_c` at 4,619 reads the retained `sgSketch` class at 4,824 and allocates object 334 in ResolvedFeatures. It contains one point at `(0,0)`, zero lines and zero value dimensions. Its one logical relation has subtype 17 and points through `sgPointHandle` object 335 to point index zero. The native meaning of subtype 17 remains open.

Starting at byte 5,085, the Origin presentation branch consumes two typed empty `suObList` records using the class retained from Config-0. They begin at 5,099 and 5,275 and allocate slots 336 and 337. A separate historical baseline native trace at Git commit `2cb8eb9ad078f9afb5fa8386f00513e7c3674a73` preserves the primitive reads in the `programs/resolved/default/Methods` operation tables. The historical second list at 5,586 and the enclosing profile's next null at 5,649 put the same 63 bytes between those boundaries. The recorded primitive fields between the two lists corroborate the current run of short counters, the bent reference array, empty UTF-16 label, line presentation state, zero point vector and empty arrays. The current first list begins two bytes earlier than the historical alignment would predict. The modern guard checks the additional zero short before the read sequence aligns again. The current sketch-state dword at 5,121 is 2, compared with 1 in that historical record. The replay checks each field and count of the modern shape, including the absent kernel packet after the last list. [Historical pointer trace](../../../../re/data/segments/Streams/SegmentsBaseline.json), [historical primitive-trace method](../../../../re/solidworks/records/Resolvedfeatures.md#9-reproduction)

The sketch ends at the enclosing profile's next null pointer at 5,338. The following typed `moCompRefPlane_c` at 5,340 allocates slot 339, then a `moUnitComponent_c` in slot 340 refers to the retained part object at slot 2. The component's saved feature ID 2 resolves to the previously read Front Plane object 321. The component carries no embedded plane, and the following transform is the identity. The outer feature-state word varies across the edited captures, and its interpretation remains open. All eleven reach the exact end of Origin at 5,525 with next map index 341.

## Profile checkpoints

The offline profile read begins at the saved schema-1 `moProfileFeature_c` declaration for RectangleSketch and the corresponding class reference for CutSketch. Each outer frame supplies its own typed name, feature ID and common feature fields. The separate native observation supplies the archive class and object identities across the stream boundary. The three historical profile traces place the early null pointer six bytes before the sketch child. The modern common fields end four bytes before that early pointer in each checked profile. The replay checks the intervening dword, typed null and final dword, then reads the sketch backreference at the exact licensed cursor. [Historical baseline trace](../../../../re/data/segments/Streams/SegmentsBaseline.json), [historical ring trace](../../../../re/data/segments/Streams/SegmentsVendorRing.json)

| Capture | Profile | Native ID | Profile token | Early null pointer | Typed sketch slot | Config-0 object |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Baseline A | RectangleSketch | 26 | 5,525 | 5,736 | 5,742 | 155 |
| YZ | RectangleSketch | 26 | 5,525 | 5,736 | 5,742 | 155 |
| Baseline A | CutSketch | 35 | 9,417 | 9,594 | 9,600 | 74 |
| YZ | CutSketch | 35 | 9,487 | 9,664 | 9,670 | 74 |

The sequential walk reads `moProfileFeature_c` at 5,525, allocates class slot 341 and object 342, then reaches the RectangleSketch backreference at 5,742. All eleven resolve it to the `sgSketch` previously allocated at slot 155 in Config-0. The cursor after that pointer is 5,744 with next map index 344. The baseline A and YZ results agree with the independent pointer witnesses.

## RectangleSketch return and file reference

The modern profile continuation reads one `moSketchChain_c`, which reaches byte 5,851 with edges `[1, 2, 3, 4]` and next map index 346. The embedded kernel body, edge tables and contour map are empty in this profile. The local `moCompRefPlane_c` at 5,874 refers to the retained part and one of the previously decoded principal planes. The reader compares the support name and the stored transform to independent SOLIDWORKS measurements for all eleven captures. Ten use Front Plane and the identity transform. The YZ capture uses Right Plane and the stored YZ basis.

After the profile support, the reads at `sldmodu+0x9dc195`, `0x9dc204`, `0x9dc470`, `0x9dc4ba`, `0x9dc582`, `0x9dc5c6` and `0x9dc638` frame the two cached trim arrays at `0x9dc67c` and `0x9dc693`. On the recorded build the simple surface and left and right trim classes share the surface identifier base at `0xa67a20`. The simple surface loader at `0xa69930` adds one dword after the base, and the trim loader at `0xa67990` adds two. The single simple surface refers back to the current RectangleSketch and allocates `moFR_c` class slot 350 and `moExtObject_c` object slot 353. Both allocations agree with the independent baseline A and YZ live map observations. The four trim edges share that file reference and native feature ID and time. The edge IDs cover the saved chain once. YZ changes the trim class and ID order, while the other ten captures share the same order. [Licensed face map](SolidWorksFaceOccurrence.md)

The file reference loader at `sldarchiveu+0xd8e0` uses the shared file fields at `0xe940` and the inline configuration-name reader at `0x181b0`. It materializes two string handles for the saved file path and title. Their widths come from the strings in each archive. The report includes the file reference allocation, offsets and shared timestamp. The final profile state dword follows the trim arrays through `sldmodu+0x9dc7e1`. The subsequent schema-1 `moExtrusion_c` tag is visible at the derived cursor, with next index 367 in every capture.

| Capture | File reference span | RectangleSketch return |
| --- | ---: | ---: |
| Baseline A | 6,072–6,207 | 6,380 |
| YZ | 6,144–6,277 | 6,450 |
| Through-all | 6,072–6,205 | 6,378 |
| Baseline B, six parameter edits and inch display | 6,072–6,435 | 6,608 |

## BlindBoss ownership and end-specification boundary

The extrusion allocates object 368 and reads the saved name `BlindBoss` and feature ID 34. Its one-entry resolved node list points back to RectangleSketch object 342. The atom reader's first transfer array at `sldmodu+0x9ca56b` resolves an existing Config-0 `moAtom_c` at slot 58 or 59. Its second array is empty. The first inline chooser enters at `0x9cac72`, the empty second at `0x9cada3` and the repeated chooser at `0x9caec6`. Each chooser references the current boss through the typed owner load at `0x112b3a1`.

The first chooser materializes two cap references with occurrence codes 0 and 1. Each cap and four boundary segments carry the same derived file reference, feature ID and time. They allocate the previously witnessed face class slots 372, 374 and 377. The repeated chooser reads the same cap and boundary objects using shared-map backreferences. Its bounding centre and scale are identical to the first chooser's fields. For baseline A, the boss's occurrence 1 carries ordered boundary IDs `[4, 1, 2, 3]`. For YZ, it carries `[4, 3, 2, 1]`. Both the feature and time tuple and the boundary order match the separately licensed CutSketch support observations. The preserved [face-support replay](SolidWorksFaceOccurrence.md) starts independently at the CutSketch sketch pointer.

The partition marker and guarded atom fields lead to the body feature's optional assembly and component references, its empty array and its final dword. The `moEndSpec_c` loader at `sldmodu+0x9cf540` reads the null direction pointer, the single-end, flip and reverse fields and the null keep-piece pointer before the two termination codes. All eleven independently measured boss operations agree with the resulting forward single-direction blind specification. The typed depth-dimension token at the next cursor matches the `moDisplayDim_c` read at `0x9cfa51`, resolves the Config-0 `moDisplayDistanceDim_c` class and leaves next map index 406. The default command stops at this token. [End specification field definitions](../../../../re/solidworks/records/Serialize.md#1-moendspec_c--confirmed)

| Capture | Boss entry | Atom end | End specification | Depth dimension token |
| --- | ---: | ---: | ---: | ---: |
| Baseline A | 6,380 | 7,426 | 7,436 | 7,477 |
| YZ | 6,450 | 7,496 | 7,506 | 7,547 |
| Through-all | 6,378 | 7,424 | 7,434 | 7,475 |
| Baseline B, six parameter edits and inch display | 6,608 | 7,654 | 7,664 | 7,705 |

## Continuous CutSketch link

Run `python re/solidworks/archive/ResolvedEntry.py --through-cut` to extend the same replay through the boss depth parameter and the CutSketch link. The JSON report SHA-256 is `13d9dc98c2ea59bc4436b1fb99a28b9daa92a3d255786bf3379d4323b7e3cd36`.

The depth display at slot 406 allocates a `moFeatureDimHandle_c` at 408 and a `ParallelPlaneDistanceDim_c` at 410. The dimension uses the existing `moLengthParameter_c` class and allocates parameter object 411. The authored length is `depth_mm` and equals 0.010 m in ten captures and 0.012 m in the depth edit. Both saved display copies agree with the parameter. The replay also checks the name, system value and extrusion depth against independent SOLIDWORKS measurements for every capture.

The historical native field trace at `2cb8eb9ad078f9afb5fa8386f00513e7c3674a73` in `programs/resolved/default/Methods` accounts for the scalar types, strings and pointer order. The historical handle body and modern body use the same field sequence with the appropriate generation word. In the modern stream the length parameter and favorite handle use retained class references, and the parameter name is longer. The typed walks reconcile those changes before reading the parallel-plane points, transforms and annotation fields. The exact receipt and checked generation scope this presentation shape. Some appearance and trailer fields have measured widths and unassigned meanings. [Historical pointer trace](../../../../re/data/segments/Streams/SegmentsBaseline.json), [typed handle and display layouts](../../../../re/solidworks/records/FeatureBody.md#6-mofeaturedimhandle_c--eight-children-with-a-closed-generation-gate)

After the display returns, `moFromEndSpec_c` at slot 415 records type 0 for the sketch-plane start. The enclosing boss returns at the next earlier-profile class reference. The walk allocates CutSketch at 416, reads its own feature ID and resolves its sketch pointer to Config-0 object 74. The cursor preserves next map index 418. Baseline A and YZ match their independent licensed profile anchors exactly. The replay stops immediately after the CutSketch sketch pointer. [Independent support body replay](SolidWorksFaceOccurrence.md)

| Capture | Depth display return | CutSketch entry | Config-0 sketch backreference | Cursor after link |
| --- | ---: | ---: | ---: | ---: |
| Baseline A | 9,284 | 9,417 | 9,600 | 9,602 |
| YZ | 9,354 | 9,487 | 9,670 | 9,672 |
| Through-all | 9,282 | 9,415 | 9,598 | 9,600 |
| Baseline B, six parameter edits and inch display | 9,512 | 9,645 | 9,828 | 9,830 |

## Continuous CutSketch support

Run `python re/solidworks/archive/ResolvedEntry.py --through-support` to carry the derived Config-0 and ResolvedFeatures map through the CutSketch support in all eleven captures. The JSON report SHA-256 is `52e1dfee9c4c633104e9624c2ea24139ed5a6b792b3a0e36696372c14a0e0264`. The independent [face-support replay](SolidWorksFaceOccurrence.md) retains its own stream anchors, licensed map and output digest.

The sequential reader continues from the resolved CutSketch pointer into the chain, framed kernel packet, four typed profile edges and embedded supporting plane. These fields use the classes and object references materialized by the preceding walk. The loaded support cap and four profile face references carry the same file object, feature ID, timestamp and positive occurrence as the earlier BlindBoss cap. The ordered support boundary IDs also match the boss cap. This comparison holds for all eleven captures. Independent reopen measurements identify face support in every capture. The decoded world normal agrees with the measured sketch transform in each case, with +X for YZ and +Z for the remaining ten.

Baseline A and YZ match the independently licensed kernel packet, reference plane, nested face, map and support return boundaries. Baseline A also matches the licensed atom span. This invocation stops after the support at map index 475 in every capture.

| Capture | Support entry | Support return | Ordered cap boundaries |
| --- | ---: | ---: | --- |
| Baseline A | 11,531 | 12,588 | `[4, 1, 2, 3]` |
| YZ | 11,595 | 12,724 | `[4, 3, 2, 1]` |

## Complete cut operation and resolved list

Run `python re/solidworks/archive/ResolvedEntry.py --through-operation` to read the rest of CutSketch and the final cut feature in all eleven pinned captures. The report SHA-256 is `9ecde927c05c451e4f703eaf101748d75165d0a80d5f6db5f12a3615a328f257`. The earlier command variants retain their recorded digests.

CutSketch's remaining placement matches all thirteen measured placement values, including the local translation of −0.012 m in the boss depth edit and −0.010 m in the other saves. The auxiliary transform is the identity. The one cached trim surface and twelve segments refer to the reached CutSketch, share its feature reference and reuse the previously allocated file object. At the CutSketch return the next allocation is class 501, `moICE_c`. The cut object 502 selects CutSketch object 416 and carries its own transfer object as well as a reference to the earlier boss transfer.

The `moCompSolidBody_c` branch at `sldmodu+0xa63620` loads the prior boss face and counted body identifier. The cut chooser records keep the same-document references to the boss and cut. The two three-integer surface types share the base dispatch at `0xa63480`, with separate three-dword continuations at `0xa6abb0` and `0xa6a840`. The repeated chooser reads the identical materialized surface objects in order. The atom tail and body feature fields lead to the retained `moEndSpec_c` class, consistent with the common extrusion loader at `0x9d0930`. [Result body layout](../../../../re/solidworks/records/FeatureBody.md)

Ten cuts use one forward blind direction. Their typed depth display and named `cut_depth_mm` parameter read 0.004 m, or 0.005 m in the cut-depth edit. The through-all capture has end condition 1 and a null depth pointer. Both terminations start from the profile plane, as recorded by the retained `moFromEndSpec_c` type 0. The replay compares the operation name, direction, end condition and named depth to independent reopen measurements, then consumes the four-byte stream footer and checks the exact end of the data. The bounded kernel payload and unnamed presentation fields remain research evidence under the pinned build and receipt. [End specification fields](../../../../re/solidworks/records/Serialize.md#1-moendspec_c--confirmed)

| Capture | CutSketch return | Cut end-spec entry | Cut return | Resolved extent | Next map index |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline A | 12,994 | 14,351 | 16,252 | 16,256 | 557 |
| YZ | 13,202 | 14,559 | 16,460 | 16,464 | 557 |
| Through-all | 12,993 | 14,320 | 14,462 | 14,466 | 550 |
