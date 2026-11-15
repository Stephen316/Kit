# P04 root atoms and first sketch allocation

The strict MO 19000 configuration walk derives `sgSketch` class index 73 and object index 74 from the witnessed native map in all eleven P04 discovery captures. The first relation's `moSkDimHandleValG2_c` owns the archive call that materializes this sketch. The previously inventoried `CutSketch` profile reference targets the same object index. [Native archive map](P04ArchiveWalk.md#native-root-map), [profile ownership inventory](P04SketchResidence.md#cross-stream-sketch-ownership)

The offline walk uses the [pinned eleven discovery inputs and PE hashes](P04ArchiveWalk.md#inputs), the [two verified native context branches](P04ContextWalk.md#licensed-context-witness), and the layout engine's existing tag and CString readers. It refuses references to indices that have not been allocated with the correct kind. Its positioned reads derive the boundaries from nested serializers and counts. No recorded fixture offset or sketch index is used to place a read.

## From model data to the relation manager

1. After the MO 19000 model-data body, the part loader calls `moBodyVizProps_c` at `sldmodu+0x10eea6f`. The exercised restore at `0x10fda90` reads the two dword counts at `0x10fdaef` and `0x10fdc66`. Both lists are empty. The caller reads four version-gated dwords at `0x10eeaa9`, `0x10eeb0b`, `0x10eeb61`, and `0x10eebb7`. The key-set read at `0x10eec2d` consumes a dword count and two dwords per key. The count is zero.
2. The native split helper at `0x10ceed0` reads a signed length at the start of each root split. In all eleven streams, the first length ends at the boundary reached by the body-visualization and animation-key fields. The length at that boundary accounts for all bytes after its own word. The first split's destructor stores the load array and counter at `0x10cf828` and `0x10cf868`. The second split restores them at `0x10cef81` and `0x10cefc8`. The second split begins with the empty inline `moNodeList_c` and its trailing dword. Follow the list call at `0x10394a3` to slot 5 at `0x10375a0`, which reads the short archive count and dword.
3. The model's first inline manager call at `0x10f19ce` invokes `moAtomManager_c` slot 5 at `0xbaea00`. It reads two dwords, with the second giving the atom count, and reads that many typed `moAtom_c` pointers at `0xbaeba4`. A final dword follows at `0xbaeca4`. All eleven inputs have two atoms. The first defines class 57 and object 58. The next uses class 57 to create object 59. Baseline A and baseline B swap the two atom payloads while preserving the allocation sequence.
4. Atom slot 5 at `0xbaece0` invokes the inherited lightweight node serializer. Each observed atom has a null node name, four dwords, a framed CString, an absent optional child-list flag, a null visual-properties pointer and an empty resolved node list with its dword trailer. The atom body then reads six dwords ending in body mode, zero in these captures. This mode skips both alternative embedded body branches. Three dwords follow at `0xbaf389`, `0xbaf3af`, and `0xbaf3cc`. The clear context mask takes the three-dword branch at `0xbaf31c`, `0xbaf337`, and `0xbaf347`. The generation-gated dword at `0xbaf360` closes each body.
5. The model's second inline manager call at `0x10f1a24` invokes `moGhostBodyIdManager_c` slot 5 at `0xdc3cf0`. The reader takes one dword and a packed count whose upper nibble holds flags. Each of the two inline `moGhostBodyObject_c` bodies starts with four dwords, followed by a dword count and dword entries at `0xdc41d0` and `0xdc41ee`. The geometry-object presence and point counts at `0xdc4241` and `0xdc429e` are zero. The next archive action at `0x10f1b04` reads the typed `moRelMgr_c` pointer.

## First relation to first sketch

| Record | Native class/object indices | Baseline A tag offset |
| --- | --- | ---: |
| `moRelMgr_c` | 60/61 | 3,336 |
| `moRelation_c` | 62/63 | 3,354 |
| `moRelEquationSide_c` | 64/65 | 3,552 |
| `moRelDimension_c` | 66/67 | 3,579 |
| `moDimRefWrapper_c` | 68/69 | 3,605 |
| `moSkDimHandleValG2_c` | 70/71 | 3,636 |
| `moUnitComponent_c` class reference | 43/72 | 3,662 |
| `sgSketch` | 73/74 | 3,772 |

The relation manager at `sldmodu+0x11f7f70` opens the relation list at `0x11f7f8a`. The list has short count 2. The relation serializer at `0x11f8400` reads equation text as a CString, then a u16 and a dword, then reads the left-hand side at `0x11f866f`. The side serializer at `0x11f7a80` opens its inline list of one entry at `0x11f7aab`. The dimension serializer at `0x11f7810` reads an empty inline list, a null component-reference pointer at `0x11f78ab`, and the dimension wrapper. The wrapper at `0x112dc30` reads the value as a double and calls the base reference serializer at `0x1134b50`. Its pointer read at `0x1134f65` materializes the dimension handle.

The dimension handle at `0x16f4da0` calls its base at `0x16e8570`. The component-reference loader at `0xa66160` reads the unit component at `0xa665af`. That class reference creates object 72 and its child resolves to the existing part at slot 2. The modern scalar run after the unit component is 20 dwords, ending with the MO generation read at `0xa66eda`. The optional payload flags are clear. The loaded handle then reads an absent transform u16, four null pointers, a byte, two null pointers, a dword, another absent transform u16 and a final dword. The ordinary local-sketch branch reads the next pointer at `0x16f50b3` and explicitly checks `sgSketch` at `0x16f50b9`. The sketch's class definition allocates indices 73 and 74.

| P04 discovery group | Second split length field | First atom | Relation manager | First sketch | First missing layout |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline A | 3,054 | 3,072 | 3,336 | 3,772 | 4,537 |
| Baseline B, six edits and inch display | 3,092 | 3,110 | 3,374 | 3,810 | 4,575 |
| YZ and through-all | 3,052 | 3,070 | 3,334 | 3,770 | 4,535 |

The walk reaches 77 typed rows in each capture. The current table stops at `moCompSketchEntHandle_c` slot 0 inside the first sketch, with no run defined for MO 19000. Its position in the sketch follows four lines and the first sketch relation. The source-derived allocation verifies the first sketch's identity. The complete first sketch span, second sketch allocation and complete resolved profile traversal still need typed coverage.

## Reproduce

Verify the capture and PE hashes as in the [root map note](P04ArchiveWalk.md#reproduce-and-extend). Use the same verified root seed and context as in the [model-data walk](P04ContextWalk.md#strict-typed-continuation). Follow the listed split, manager and dimension-handle calls in the matching loader, and layer the guarded fields onto the existing `Archive.Segment` layouts. The scratch `P04AtomWalk.py` uses the counts and widths above to derive the offsets and prints each allocation through the first unsupported slot. The partial sketch row covers the walked lead alone. [Archive reader](../../../src/convert/adapters/solidworks/container/Archive.py), [layout table](../../data/Layouts/ClassLayouts.json)
