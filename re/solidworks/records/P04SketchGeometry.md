# P04 generation-19000 sketch geometry

The strict configuration archive walk recovers the first `sgSketch` point and line groups, four length dimensions, and four logical member relations in all eleven pinned P04 discovery captures. It carries the same typed archive map from the [first sketch allocation](P04AtomWalk.md#first-relation-to-first-sketch). The first sketch is the cut sketch. Its stored dimensions and points respond to the controlled cut parameter and sketch plane changes.

## Inputs and checks

Use the [pinned capture, receipt, and binary hashes](P04ArchiveWalk.md#inputs) and the [witnessed root context](P04ContextWalk.md#licensed-context-witness). The walk is restricted to MO generation 19000 and the exercised archive context. It validates the object schema, class definition and reference kinds, and the expected type of each pointer. It bounds counts by the remaining stream and stops when an inactive group or optional field differs from the supported path. The allocation and cursor derive from the framing. The offsets and map indices below are outputs measured against the captures.

| Capture group | Sketch body | End of points | End of lines | End of value dimensions | End of first logical group | Next map index |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline A | 3,786 | 4,936 | 5,400 | 6,176 | 6,402 | 123 |
| Baseline B, six parameter edits and inch display | 3,824 | 4,974 | 5,438 | 6,214 | 6,440 | 123 |
| YZ and through-all | 3,784 | 4,934 | 5,398 | 6,174 | 6,400 | 123 |

## Geometry and dimension fields

1. The `sgSketch` load branch at `sldmodu+0x1451fc8` reads the signed dword point count through the modern count helper at `0x1462a00`. After each u16 subtype at `0x14524f7`, both observed subtype paths call the inline point serializer at `0x144d9b0`. The four corner points use subtype zero and the origin uses subtype one. Its member base at `0x1441500` reads two dwords, an inline visual record, a dword and a u16 compact flag, the guarded width extension, a typed external entity pointer, and the remaining member flags and scalars. The `ff ff 1f 00 03` prefix comes from the two u16 and one byte read by the visual helper at `0x100ef20`. The point's 2D flag at `0x144e0c1` selects two doubles at `0x144e0ed`. The origin's external entity follows the [typed external-reference chain](P04AtomWalk.md#first-sketch-continuation).
2. The signed dword line count at `0x14526ff` gives five entries. The observed mode-zero line call at `0x1452a36` invokes `0x1448d30`, whose curve base at `0x144e9c0` reads the member base and two point indices at `0x144ecb3` and `0x144ecf0`. The short-index escape `0xffff` selects a dword. Baseline A stores a flagged first record with endpoints `(0,1)` and four perimeter records `(0,3)`, `(0,2)`, `(2,1)`, `(3,1)`. The member indices identify the records independently of that ordering.
3. The intervening eleven modern dword-count geometry groups are empty. The dimension helper called at `0x1455b5c` reads an empty `sgValG1Dim` group at `0x145f203` and the u16 `sgValG2Dim` count at `0x145f505`. The typed read at `0x145f61f` dispatches the three observed distance classes to slot 5 at `0x145d120`. Its base `Dimension_c` reads the `moLengthParameter_c` pointer and the dimension ID. The parameter at `0x1035bd0` reads a typed `moNodeName_c`, then its own scalar and optional override flag. The observed override is absent. The distance body reads an absent transform and two typed point-handle pointers at `0x145d458` and `0x145d48f`.
4. The u16 `sgValG3Dim` and `sgOffsetDim` counts at `0x145f855` and `0x145fe13` are zero. The generation gate at `0x145fbd2` skips the legacy `sgArcLenDist` group. The u16 `sgLogG1Dim` count at `0x1460071` is four. The inline serializer invoked at `0x146018a` reads an `sgDim` base with absent length parameter and tolerance, two u16s, and a typed `sgLineHandle` at `0x14499b5`. The four class references allocate objects 119 through 122.

Baseline A has four corners at `(15,6)`, `(25,14)`, `(15,14)`, `(25,6)` mm and the origin at `(0,0)`. The YZ capture has corresponding coordinates `(-6,15)`, `(-14,25)`, `(-6,25)`, `(-14,15)` mm. The two position dimensions also exchange horizontal and vertical classes in YZ while keeping their native IDs, names and lengths.

| Native ID | Parameter | Baseline length (mm) | Observed changed lengths (mm) |
| ---: | --- | ---: | --- |
| 36 | `cut_width_mm` | 10 | 12 in the cut-width edit |
| 37 | `cut_height_mm` | 8 | 10 in the cut-height edit |
| 39 | `cut_left_mm` | 15 | 17 in the boss-width edit and 14 in the cut-width edit |
| 40 | `cut_bottom_mm` | 6 | 8 in the boss-height edit and 5 in the cut-height edit |

The values come from binary doubles in metres. The inch-display control retained the same physical lengths to the captured floating-point precision.

In all eleven captures the four `sgLogG1Dim` records in each sketch resolve through typed `sgLineHandle` references to the four perimeter member identities. The `sgDim` serializer's signed dword read at `sldmodu+0x1444b58` populates its type field at `+0x80`. The geometric satisfaction check reads that field at `0x66a08f`. Its dispatch selects the local Y-coordinate difference for code `4` and the local X-coordinate difference for code `5`, giving horizontal and vertical respectively. The following `sgLogDim` short reads at `0x1449829` and `0x1449888` still produce `(65534, 0)` in the observed records.

The offline report checks the typed value and target against the independently reopened SOLIDWORKS relation observations for both sketches. Baseline A and YZ give `2` vertical, `1` horizontal, `4` vertical and `3` horizontal. All 88 axis relation bindings and all 66 ordered distance operands match. The member base puts the dword after the visual properties into its field at `+0x20` through `sldmodu+0x1441db0`. For every decoded point, that stored dword equals its measured relation incidence count. The rectangular profile's two residual incidences occur on distinct point IDs at the same coordinates. [Sketch evidence report](../../../Documentation/Changes/Research/Readers/SolidWorksSketchGeometry.md), [pinned native measurements](../../automation/PairedCaptures/P04/solidworks-c1986308375a/measurements.json)

## Continue the walk

Seven further empty u16-count groups precede the typed `suObList` read at `sldmodu+0x14611a1`. In baseline A, the list tag starts at byte 6,416. The short `su_CObList` count is four. The first `moDisplayDistanceDim_c` tag starts at byte 6,432. Its matched slot 5 is `0x16eee40`, which first calls the display dimension base at `0x16ea130`. The modern load branches in that base are the next offline boundary. The older wildcard runs in the [layout table](../../data/Layouts/ClassLayouts.json) do not qualify the version-19000 display dimensions. The later sketch fields and traversal into the second sketch remain open in the offline walk.

Reproduce the partial walk with the scratch `P04SketchWalk19000.py` and the prior files described in the [root atom walk](P04AtomWalk.md#reproduce). Start from the first allocated sketch body, replay the matching archive calls above, and keep one typed map when taking each inline or object branch. Confirm all eleven outputs, then continue with the typed list, display-dimension base and remaining sketch groups. Validate the final object boundary and map count against the independent native measurements. The baseline A sketch body ends at byte 12,532 with next map index 147, and YZ ends at 12,530 with the same next index.

## Native object calls in the baseline A sketches

A fresh owned session opened the read-only baseline A capture on build `34.4.1.1011`, closed the capture normally, and exited with its source hash unchanged. The observed `Contents/Config-0` buffer is 42,879 bytes with SHA-256 `e40cdd1e562a9e501a0a29ac252745d5c5cac6a7265ef924ccef4f5d078b34ab`. The matching installed image pins are in the [root map inputs](P04ArchiveWalk.md#inputs).

The two `sgSketch` serializer hooks at `sldmodu+0x144f790` and `0x1457e80` match the archive buffer and sketch object identity at entry and exit. Entry verifies that the native load map's most recent slot holds the same object pointer passed to the serializer. Between those hooks, the breakpoint at the ordinary `su_CArchive::ReadObject` entry `swccu+0xa550` records only calls on the selected archive object and same buffer within the active sketch span. The object hook is disabled between sketches. All hooks are disabled at the second exit.

| Sketch object | Body interval | Next map index at entry and exit | Null reads | Class definitions | Class references | Existing object references |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 74 | `[3786,12532)` | 75 to 147 | 153 | 14 | 44 | 5 |
| 155 | `[12923,18277)` | 156 to 200 | 102 | 0 | 44 | 3 |

All 365 object call positions match the observed buffer tags. The offline prefix predicts all 92 positions in the first sketch before the display list. A class definition advances the map by two, and an existing class reference advances it by one. Null and existing-object references leave the counter unchanged. Each transition agrees with the next native call and the final map count. In the first sketch's remaining span, the new definitions are `suObList` at byte 6,416 (class/object 123/124), `moDisplayDistanceDim_c` at 6,432 (125/126), `moFavoriteHandle_c` at 7,463 (128/129), and `moSketchRegion_c` at 12,428 (140/141).

The interval `[12532,12923)` lies outside the recorded sketch windows. The native index advances from 147 to 156 across that interval, with the final allocation materializing the second sketch at index 155. Eight preceding map slots still require an intervening source walk. The nested calls witness positions and allocations. The offline reader still needs the versioned scalar, string, and array framing between them.

The scratch verifier rejects a mismatched full archive digest, unexpected span or map boundaries, and object tokens that differ from the observed buffer. Its normalized `SketchObjectsSummary.json` records the capture hash, object call offsets, map counters, token words and module-relative caller offsets. The verified normalized file in the baseline A scratch trace has SHA-256 `d724ad7b0c0d7daed50adf96028c08a3f83e5afde5e841ca25506cd6baf3939a`.
