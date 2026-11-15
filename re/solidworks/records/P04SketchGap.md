# P04 allocation of the second configuration sketch

A single read-only baseline A session on build `34.4.1.1011` observes how the configuration load map reaches the second `sgSketch`. The `Contents/Config-0` buffer matches the pinned baseline A SHA-256 `e40cdd1e562a9e501a0a29ac252745d5c5cac6a7265ef924ccef4f5d078b34ab`. The owned process closes normally with the source capture hash unchanged. [Capture and image pins](P04ArchiveWalk.md#inputs), [native sketch windows](P04SketchGeometry.md#native-object-calls-in-the-baseline-a-sketches)

The first `sgSketch` entry at `sldmodu+0x144f790` verifies that load map slot 74 holds the serializer's object. Its matching return at `0x1457e80` sees byte 12,532 and next map index 147 on the same archive object and buffer. At that point the `swccu+0xa550` object hook enables for the interval `[12532,12923)` on that archive and buffer alone. On the second `sgSketch` entry at byte 12,923, slot 155 holds the incoming serializer object and the next map index is 156. The second entry disables all three hooks.

| Config-0 byte | Native read or allocation | Map result |
| ---: | --- | --- |
| 12,538 | Enclosing reference wrapper's null child | Unchanged |
| 12,720 | First `moRelEquationSide_c`'s parent reference read, returning to `0x11f7b9c` | Existing `moRelation_c` object 63 |
| 12,722 | Following `moRelEquationSide_c` class reference | Class 64, object 147 |
| 12,726 | First entry in the following side's operand list | `moRelOperator_c` class 148, object 149 |
| 12,769 | Second operand | Operator class 148, object 150 |
| 12,793 | Third operand | `moRelDimension_c` class 66, object 151 |
| 12,799 | Dimension reference wrapper | `moDimRefWrapper_c` class 68, object 152 |
| 12,809 | Wrapper's sketch-dimension handle | `moSkDimHandleValG2_c` class 70, object 153 |
| 12,811 | Handle's unit component | `moUnitComponent_c` class 43, object 154 |
| 12,813 | Unit component's root part reference | Existing `moPart_c` object 2 |
| 12,921 | Local sketch pointer read | `sgSketch` class 73, object 155 |

All 18 native object reads match archive tags and map transitions. The eight null pointer reads leave the map unchanged. The following side has short count eight, so its third operand opens the second sketch while five operands remain.

## Derive the interval offline

The matching loader can continue from the first sketch return when the position and typed map at that return are available. The dimension handle first reads one dword at `sldmodu+0x16f50e7`. Its enclosing reference wrapper reads a u16 and the null component pointer at `0x113503d`, followed by the guarded modern tail of two dwords, two absent-transform u16s and eleven dwords. A separate image unwind fragment starting at `0x11f7942` completes the enclosing `moRelDimension_c` serializer. Its `0x11f7948` call goes to `0x11f7980`, which reads a CString and four dwords after the generation guard. That dimension name is the first copy of `"cut_left_mm@CutSketch"` at byte 12,596. The equation side independently reads its own CString at `0x11f7b2d`, then two dwords and the parent relation at `0x11f7b96`.

The following side uses its inline `suObList` count. `moRelOperator_c` slot 5 at `0x11f7770` calls the same `0x11f7980` string-and-four-dword helper. The typed dimension operand then reads its empty inline list and null component pointer, allocates the dimension wrapper, and takes that wrapper's sketch-dimension handle. The [first allocation's component and local-sketch path](P04AtomWalk.md#first-relation-to-first-sketch) applies again. The cursor reaches the second sketch via the class reference without a fixed offset advance or a fixed class ID. The offline framing matches all 18 native pointer events and the entry counter.

Starting at the measured second entry, the same guarded offline geometry parser reads five points, five lines, two length dimensions, and four logical member relations. Its 74 pointer call positions match the separate native sketch-body trace. The group ends are 13,954, 14,418, 14,776 and 15,002 respectively, with next map index 184. The points outline a rectangle from `(0,0)` to `(40,20)` mm. The two distance dimensions are `width_mm` ID 27 at 40 mm and `height_mm` ID 28 at 20 mm. The first sketch's dimension names and geometry identify its different cut rectangle. [First sketch geometry](P04SketchGeometry.md#geometry-and-dimension-fields)

Reproduce the native checkpoint with `SketchGapBaseline.cdb` and `VerifySketchGap.py` in the scratch trace directory, using the same owned read-only launch and source hash checks as the [root archive witness](P04ArchiveWalk.md#native-root-map). Verify the module and buffer identities before accepting the call positions. The normalized `SketchGapSummary.json` records the 18 offsets, read kinds, map counters and module-relative callers with SHA-256 `06759925a980ee620c905ee8712518a7e2fb68d1e4c7aeccb3c69823b100de5b`.

Run `python re/solidworks/archive/SketchEvidence.py` to reproduce the offline geometry report from the root with only repository inputs. The committed research display layout carries 124 typed pointer steps for the first sketch and 73 for the second. The second frame begins with seven short fields, including two absent pointer children, before its first display step. The reader checks the exact build and generation, inline fields, framed list counts, and the kind and class at each step. Both complete sketch bodies match their licensed bounds in baseline A and YZ, and all eleven captures traverse both frames. [Research command and scope](../../../Documentation/Changes/Research/Readers/SolidWorksSketchGeometry.md)

## Follow the second sketch return

After the second sketch returns at map counter 200, the active dimension handle reads its final dword. The wrapper and operand finish with the same fields used after the first sketch. The enclosing side then reads five remaining operands and resolves its parent relation. The last operand `moRelValue_c` uses the same text-and-four-dword serializer as `moRelOperator_c`. The relation finishes with two dwords, a CString and three dwords. The manager's remaining relation opens another pair of equation sides, followed by the same trailer.

The manager reads an empty parameter list, a CString, a dword, one compact `su_CTime`, two dwords, a second empty list, and two final dwords. The last dword is the count of an empty parameter array. These sizes follow the `moRelMgr_c` load path at `sldmodu+0x11f7f70`. The two relations return to `0x11f8505`, and the manager read returns to its owner at `0x10f1b09`.

| Capture | Second sketch return | First relation return | Second relation return | Manager return |
| --- | ---: | ---: | ---: | ---: |
| Baseline A | 18,277 / 200 | 18,971 / 209 | 20,361 / 230 | 20,393 / 230 |
| YZ | 18,275 / 200 | 18,969 / 209 | 20,359 / 230 | 20,391 / 230 |

Each cell gives the full Config-0 byte offset and next map index. The guarded offline traversal matched all 73 distinct typed pointer positions, tokens and counters between the second sketch return and manager exit in each capture. The native traces recorded 75 and 76 calls respectively, including repeat reads at the same position and counter. Both owned processes exited cleanly and preserved the original source hashes. The normalized baseline A witness SHA-256 is `f7b17b369cfc512855189ddca7db5a20ff9a38ec9d992d8950a7297418a36724` and the YZ witness SHA-256 is `4986318276d6223e69cd74ba0fe6533fe65ba7f2010b2acf54e970852f2db0dd`. The remaining Config-0 body and its final map handoff to `ResolvedFeatures` still require a structural walk.
