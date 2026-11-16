# Configuration root and native model title

The generation-19000 `Contents/Config-0` root can be constructed from the body after the first split dword up to the first `moVisualProperties_c` tag. The ordinary `moPart_c` class and its first split length belong to the enclosing configuration stream. The caller supplies the allocated root node ID, the native title, and the clean rebuilt part's established appearance state. The [research codec](ConfigRoot.py) admits the measured P01 and P03 standalone profile.

## Native field authority

The evidence uses installed SOLIDWORKS `34.4.1.1011`. The `sldmodu.dll` SHA-256 is `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. The `sldprtu.dll` SHA-256 is `cb1e260f8411a39dc44f4d8a6255ea585c7a5e60b223d0e69d3f51a258ee96de`. The `sldarchiveu.dll` SHA-256 is `fce17ce9f2b79e188ee0c20ca51cd36cd246d92bf2d35c2010a03f4bb5c304c6`. Addresses below are preferred image addresses.

The `moPart_c` primary table at `0x4d1222a8` uses slot 5 `0x4c227260`. Its `+0x4b8` slot is `0x4c22e1d0` and reaches the model serializer `0x4c22c480` at `0x4c22e225`. The model calls the filed-concept writer at `0x4c22c60d`. That writer's header call at `0x4c17869d` and stream-name handling lead to the separate model-header stream. It then writes the first two body dwords. The previously licensed [root seed and external object trace](../records/P04ArchiveWalk.md#native-root-map) independently identifies archive slots 1, 2 and 3.

| Order | Field | Native source |
| --- | --- | --- |
| 1 | Filed concept signed `+0xb0` and unsigned `+0xb4` | Ordinary stores `0x4c1786b8`, `0x4c1786c7`. The constructor clears both at `0x4bda4aaf`. The saved generation-19000 branch carries 0 and 19000. |
| 2 | Compact schema-1 `moNodeName_c` definition followed by title CString | `moNode_c::SerializeLWData` uses the typed operator at `0x4c178b11` for the name member `+0x18`. The name serializer at `0x4c177890` writes its one wide CString at `0x4c1778be`. |
| 3 | Clean update state, primary flags and root node ID | `0x4c178b1c` writes signed `+0xc`, also set by `setUpdateState` at `0x4b292190`. `0x4c178b38` writes unsigned `+0x28` after clearing transient bit `0x1000`. Its initial `0x40000000` is set at `0x4c03a60f`. The store at `0x4c178b47` writes signed node ID `+8`, assigned from `moHeader_c::getNewID` at `0x4bda4ba6..0x4bda4bac`. This ID is zero for the first model node, independently of the archive slot. |
| 4 | Secondary flags and empty auxiliary node string | Modern node stores `0x4c178d6a` and `0x4c178df6` read `+0x2c` and `+0x20`. The latter string starts empty at `0x4c03a5fc`. The node secondary flags start at zero within the qword at `0x4c03a603`. The successful force-rebuild path calls `setFlagOn2(0x20)` at `0x3339d4ae`. Appearance assignment calls `setFlagOn2(0x8000)` at `0x4b71b131`. The model store applies flag `0x100` at `0x4c22c602`. |
| 5 | No inline concept list | The base constructor initializes `+0x68` to null at `0x4bda486c`. Concept store `0x4c178414` emits the signed presence word before the optional list branch. The slot at `0x4c178455` writes the following visual-properties pointer. |

The model node ID and the archive allocation counter belong to separate namespaces. The caller emits the root class and split length, declares the already assigned self external object, and advances from archive counter 3 to 4. `WriteConfigRoot` then allocates the name through `ArchiveWriter`, taking class 4 and object 5. It returns at counter 6, ready for the first visual allocation. Unsupported generation, root graph IDs or profile states fail before emission.

## Replay

The command below reads only the six P01 and eight P03 capture files pinned by the original specification, native receipts and independent measurement. Its full archive and record selectors come from the shared container reader and guarded layout.

```sh
python re/solidworks/WriterResearch/VerifyConfigRoot.py --read-only
```

All 14 captures begin the semantic prefix at byte 18 and allocate the name at 26. The name has 5, 6 or 25 UTF-16 code units. The visual pointer begins at 82, 84 or 122. The nine repeated saves and edits carry a 25-unit title from the model's prior save. The writer therefore takes a native model title independently of the current file leaf. Each control reaches visual class 6 and object 7. The read-only replay SHA-256 is `b73087297e042f37f9bb4d9b87f54ae02aedd9407da1002cb31229a56de5f933`. Its compact JSON rows contain the native file SHA-256, first split length, end of prefix, prefix SHA-256, pre-visual next index and post-allocation next index.

The hosted comparison additionally reconstructs the prefix from typed state and compares the exact bytes and class map. The run can use the saved title for equality. Generated documents take the title from the caller and calculate the split length after composing its first component. The [visual constructor](ConfigVisual.md) continues through the first units-table pointer. The later configuration records and native acceptance remain open.
