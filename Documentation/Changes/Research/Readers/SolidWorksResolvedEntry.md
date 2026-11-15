# P04 SOLIDWORKS resolved entry and profile linkage

Run `python re/solidworks/archive/ResolvedEntry.py` from the repository root. The command verifies the exact P04 receipt, native files and both decompressed stream hashes for baseline A and YZ. It replays the resolved entry and the two profile records from their separate checkpoints, then writes a JSON evidence report. The report SHA-256 is `b11bdfefb1407e923e25529eb76e151d0257a49b89a5b9af117eb23b84dbbea0`. [Licensed sketch and resolved owner evidence](../../../../re/solidworks/records/P04SketchResidence.md)

The matched native handoff reaches Config-0 byte 42,879 in baseline A and 42,949 in YZ. The resolved list load begins at byte 4 with next archive index 279. The offline reader uses the completed Config-0 class and object map to start the list and to resolve the two separately anchored sketch references. The first four resolved bytes corroborate the counter at 279. The short list count at byte 4 is 21, and the first class definition begins at byte 6. [Offline map replay](../../../../re/solidworks/records/P04SketchResidence.md#offline-map-replay)

| Record | Feature ID | Object slot | Entry | Reached cursor | Next map index |
| --- | ---: | ---: | ---: | ---: | ---: |
| Comments | 8 | 280 | 6 | 203 | 282 |
| Favorites | 23 | 283 | 203 | 410 | 285 |
| History | 24 | 286 | 410 | 606 | 288 |
| Selection Sets | 25 | 289 | 606 | 825 | 291 |
| Sensors | 22 | 292 | 825 | 1,018 | 294 |
| Design Binder | 7 | 295 | 1,018 | 1,221 | 297 |

The History variant ends after two guarded folder scalars and the empty history-item count. The short count at byte 604 is the same archive field identified by the historical measured nonempty arrays. The Selection Sets body adds six guarded bytes to the common folder suffix, matching its historical post-comment width. Sensors and Design Binder use the ordinary folder suffix. The cursor reaches the next schema-1 `moDetailCabinet_c` declaration at 1,221. With the typed name seed applied, the historical generic table places a child at byte 56 inside the Comments node flags in these captures. [History array count](../../../../re/solidworks/archive/Segmentation.md#the-mohistoryfeatitemdata_c-array-count), [node field order](../../../../re/solidworks/records/Feature.md), [historical folder and profile layout](../../../../re/data/Layouts/ClassLayouts.json)

## Profile checkpoints

The offline profile read begins at the saved schema-1 `moProfileFeature_c` declaration for RectangleSketch and the corresponding class reference for CutSketch. Each outer frame supplies its own typed name, feature ID and common feature fields. The separate native observation supplies the archive class and object identities across the stream boundary. The three historical profile traces place the early null pointer six bytes before the sketch child. The modern common fields end four bytes before that early pointer in each checked profile. The replay checks the intervening dword, typed null and final dword, then reads the sketch backreference at the exact licensed cursor. [Historical baseline trace](../../../../re/data/segments/Streams/SegmentsBaseline.json), [historical ring trace](../../../../re/data/segments/Streams/SegmentsVendorRing.json)

| Capture | Profile | Native ID | Profile token | Early null pointer | Typed sketch slot | Config-0 object |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Baseline A | RectangleSketch | 26 | 5,525 | 5,736 | 5,742 | 155 |
| YZ | RectangleSketch | 26 | 5,525 | 5,736 | 5,742 | 155 |
| Baseline A | CutSketch | 35 | 9,417 | 9,594 | 9,600 | 74 |
| YZ | CutSketch | 35 | 9,487 | 9,664 | 9,670 | 74 |

The evidence keeps the list stop and both profile anchors distinct. A continuous replay still needs the remaining earlier list allocations before the first anchored profile. The [face-support replay](SolidWorksFaceOccurrence.md) carries the observed CutSketch profile from its sketch pointer through the typed supporting-face return.
