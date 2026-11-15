# P04 SOLIDWORKS resolved entry and profile linkage

Run `python re/solidworks/archive/ResolvedEntry.py` from the repository root. The command checks the exact P04 receipt, independent measurements and native file digests. It walks from the resolved list header through the RectangleSketch link for all eleven captures. For baseline A and YZ it also verifies both decompressed stream hashes and compares the separately witnessed profile links. The JSON report SHA-256 is `1dab0425819fb00e9446465930ea0538e0224836601eae08bd26d11cc17cc4fb`. [Licensed sketch and resolved owner evidence](../../../../re/solidworks/records/P04SketchResidence.md)

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

The sequential walk reads `moProfileFeature_c` at 5,525, allocates class slot 341 and object 342, then reaches the RectangleSketch backreference at 5,742. All eleven resolve it to the `sgSketch` previously allocated at slot 155 in Config-0. The cursor stops immediately after that pointer at 5,744 with next map index 344. The baseline A and YZ results agree with the independent pointer witnesses. This replay has yet to traverse the remaining RectangleSketch fields and the intervening feature records to reach CutSketch. The [face-support replay](SolidWorksFaceOccurrence.md) carries the separately anchored CutSketch profile from its sketch pointer through the typed supporting-face return.
