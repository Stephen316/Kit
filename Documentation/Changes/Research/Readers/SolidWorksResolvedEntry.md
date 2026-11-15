# P04 SOLIDWORKS resolved entry and profile linkage

Run `python re/solidworks/archive/ResolvedEntry.py` from the repository root. The command verifies the exact P04 receipt, native files and both decompressed stream hashes for baseline A and YZ. It replays the resolved entry and the two profile records from their separate checkpoints, then writes a JSON evidence report. The report SHA-256 is `f870e46bdc3799134951039f6bdc1e7c6e2761e1f7a78a6eea496cb4f244d10e`. [Licensed sketch and resolved owner evidence](../../../../re/solidworks/records/P04SketchResidence.md)

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

The typed `moOriginProfileFeature_c` at 4,619 reads the retained `sgSketch` class at 4,824 and allocates object 334 in ResolvedFeatures. It contains one point at `(0,0)`, zero lines and zero value dimensions. Its one logical relation has subtype 17 and points through `sgPointHandle` object 335 to point index zero. The replay stops at byte 5,085 with next map index 336. The remaining Origin presentation fields and the semantics of subtype 17 still need independent evidence.

## Profile checkpoints

The offline profile read begins at the saved schema-1 `moProfileFeature_c` declaration for RectangleSketch and the corresponding class reference for CutSketch. Each outer frame supplies its own typed name, feature ID and common feature fields. The separate native observation supplies the archive class and object identities across the stream boundary. The three historical profile traces place the early null pointer six bytes before the sketch child. The modern common fields end four bytes before that early pointer in each checked profile. The replay checks the intervening dword, typed null and final dword, then reads the sketch backreference at the exact licensed cursor. [Historical baseline trace](../../../../re/data/segments/Streams/SegmentsBaseline.json), [historical ring trace](../../../../re/data/segments/Streams/SegmentsVendorRing.json)

| Capture | Profile | Native ID | Profile token | Early null pointer | Typed sketch slot | Config-0 object |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Baseline A | RectangleSketch | 26 | 5,525 | 5,736 | 5,742 | 155 |
| YZ | RectangleSketch | 26 | 5,525 | 5,736 | 5,742 | 155 |
| Baseline A | CutSketch | 35 | 9,417 | 9,594 | 9,600 | 74 |
| YZ | CutSketch | 35 | 9,487 | 9,664 | 9,670 | 74 |

The evidence keeps the Origin presentation stop and both profile anchors distinct. A continuous replay still needs the remainder of Origin before the first anchored profile. The [face-support replay](SolidWorksFaceOccurrence.md) carries the observed CutSketch profile from its sketch pointer through the typed supporting-face return.
