# Blind boss display style ownership

The 94-byte appearance span reached by [`ReadDisplayOpen`](../../../src/convert/adapters/solidworks/sketch/DisplayOpen.py) in eight receipt-pinned P03 saves comes from the inherited `moDisplayItem_c` serializer. The ordered member writes identify the leading 74 bytes, and the five following signed words finish at the start of the four saved points. All addresses below are preferred virtual addresses in installed SOLIDWORKS 34.4.1.1011.

The pinned `sldmodu.dll` SHA-256 is `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. The `moDisplayDistanceDim_c` slot 5 serializer at `0x4c82ee40` calls `moDisplayDim_c` at `0x4c82a130`. The modern base call at `0x4c82a1e4` is the exported `moDisplayItem_c::Serialize` at `0x4ba4af00`. It writes the preceding object at member `+0x2d8` through `su_CArchive` at `0x4ba4b244`. The typed archive read requires that pointer to be null before the style span.

| Byte offset | Member or field | Wire type | Saved value | Store call |
| ---: | --- | --- | ---: | --- |
| 0 | `+0x3b8` | `f64` | -1 | `0x4ba4b256` |
| 8 | `+0x2e8`, first map count | `i32` | 0 | `0x4ba4b885` |
| 12 | `+0x2f0` | `i32` | 1 | `0x4ba4bc21` |
| 16 | `+0x2f8`, first line width | `i16 f32` | 0, -1 | `0x4ba4bc37` |
| 22 | `+0x2f4` | `i32` | 0 | `0x4ba4bc47` |
| 26 | `+0x304` | `i32` | 1 | `0x4ba4bc57` |
| 30 | `+0x30c`, second line width | `i16 f32` | 0, -1 | `0x4ba4bc6d` |
| 36 | `+0x308` | `i32` | 0 | `0x4ba4bc7d` |
| 40 | `+0x300` | `i32` | 0 | `0x4ba4be1e` |
| 44 | `+0x314` | `i32` | 0 | `0x4ba4be2e` |
| 48 | `+0x334` | `i32` | -1 | `0x4ba4be3e` |
| 52 | `+0x338` | `i32` | -1 | `0x4ba4be4e` |
| 56 | `+0x4a0`, `suObArray` presence | `i32` | 0 | `0x4ba4bf30` |
| 60 | `+0x318` | `i32` | 1 | `0x4ba4bf4d` |
| 64 | `+0x31c` | `i32` | 0 | `0x4ba4bf5d` |
| 68 | `+0x320`, third line width | `i16 f32` | 0, -1 | `0x4ba4bf73` |
| 74 | `+0x328` | `i32` | 0 | `0x4ba4bf83` |
| 78 | `+0x32c` | `i32` | 0 | `0x4ba4bf93` |
| 82 | `+0x4b0`, second map count | `i32` | 0 | `0x4ba4c0bd` |
| 86 | `+0x4b8`, member presence | `i32` | 0 | `0x4ba4c176` |
| 90 | Four following point records | `i32` | 4 | `0x4ba4c440` |

The first count controls the map loop from `0x4ba4b88b` to `0x4ba4b93c`. The intermediate array is serialized when archive condition 1 is clear. The measured width includes its zero presence word before the value 1 from member `+0x318`. In `sldmfcu.dll` SHA-256 `bea7d36e54929371aa9d6db9faa3210b8661a14038eb1f0fcac714c6d110e9a6`, `suObArray::serializePtr` at `0x3c8df910` stores a Windows signed long 0 for a null pointer and returns without serializing a child. The second count controls the map loop following `0x4ba4c0bd`. The helper at `0x4ba6c800` supplies the signed long presence value by testing `+0x4b8`, and a null pointer bypasses its virtual serializer.

The three line width calls resolve to `utLineWidth_c::Serialize` at `0x3c85a6e0` in the same pinned `sldmfcu.dll`. The store branch writes member `+6` with the signed short operator at `0x3c85a71e` and member `+0` with the float operator at `0x3c85a72b`. The next byte after the 94-byte span begins four `mgPoint_c::save` calls at `0x4ba4c456`. The writer then stores the count 2 at `0x4ba4c46c` and writes two vectors. The independent typed read finds the same four points and two vectors.

The three exported `moDisplayDistanceDim_c` constructors call the `moDisplayDim_c` overloads at `0x4c86c360`, `0x4c86cb40` and `0x4c86d2b0`. All three invoke the same `moDisplayItem_c` constructor at `0x4ba64990`. It sets `+0x3b8` to -1.0 at `0x4ba64bfe`, initializes the map counts to zero, and initializes `+0x4a0` and `+0x4b8` to null. The member writes at `0x4ba64b11` through `0x4ba64b7b` supply the signed word values in the table. The three constructor calls at `0x4ba64b25`, `0x4ba64b46` and `0x4ba64b67` each pass line weight enum 0 to `utLineWidth_c` at `0x3c85a5f0`. That overload writes the supplied enum to member `+6` and initializes the float at `+0` to -1.0.

The eight [receipt-pinned P03 controls](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json) include baseline, dimensional edits, inch units, YZ plane and negative direction. Their full `<d2ihf2ihf8ihf5i>` spans all have SHA-256 `5a3b29f9eea808f1984c8526c7474be07bc63b265894d6078c23860aeec1abc1`. These controls corroborate the supported normal empty branch. Appearance edits, populated child records, other display branches and native acceptance of a generated display remain unmeasured. [Enclosing depth display](BlindDepth.md)

## Terminal display item points and vectors

The plain archive store path ends `moDisplayItem_c::Serialize` with 148 bytes immediately after the 94-byte style. The count 4 is already in the last style word at `0x4ba4c440`. The first point starts at member `+0x4f0`, with a 24-byte stride and four calls to `mgPoint_c::save` at `0x4ba4c456`. The signed-long operator at `0x4ba4c46c` writes the count 2 established in `r13d` at `0x4ba4b86d`. The two calls to `mgVector_c::save` at `0x4ba4c486` start at member `+0x550`, with the same 24-byte stride. The serializer returns after the second vector and leaves the archive allocation map unchanged.

The constructor makes the four default points at `0x4ba64d63` through `0x4ba64d88`. The zero-argument `mgPoint_c` constructor at `0x31de3a20` clears three eight-byte slots. The calls at `0x4ba64d8e` and `0x4ba64da5` resolve to `mgUnitVector_c::yAxis`. The calls at `0x4ba64d9e` and `0x4ba64db5` copy that vector to `+0x550` and `+0x568`. In `sldmgu.dll` SHA-256 `3b82cfcaa13f099fca4f9741acbb11479dab7a6f20656052d5a750e61c6fee1e`, the two `save(su_CArchive&)` exports share `0x31e13a30`. The plain path writes three doubles in slot order at `0x31e13b61`, `0x31e13b6f` and `0x31e13b7d`. The separately gated database path serializes via MessagePack.

All eight exact saves decode as `<12di6d>` with four `(0, 0, 0)` points, count 2, and two `(0, 1, 0)` vectors. The span SHA-256 is `bac88f3516585d8d8532a99d9cc384405e47cbdb63beeac763384fc6973e6182`. The principal YZ and reversed-direction cases preserve the display-local +Y values. The depth parameter and its signed placement remain separately owned by the boss records.

| P03 save | First point | First text byte after vectors | First handle tag |
| --- | ---: | ---: | ---: |
| `baseline-a` | 13367 | 13515 | 13651 |
| `baseline-b` | 13595 | 13743 | 13879 |
| `edit-width_mm-41` | 13595 | 13743 | 13879 |
| `edit-height_mm-23` | 13595 | 13743 | 13879 |
| `edit-depth_mm-12` | 13595 | 13743 | 13879 |
| `units-inch` | 13595 | 13743 | 13879 |
| `plane-yz` | 13437 | 13585 | 13721 |
| `direction-negative` | 13365 | 13513 | 13649 |

To reproduce the offsets, verify the receipt, measurement digest, file sizes and file digests as in the [hosted archive check](../../../tests/Research/Archives/SolidWorksBossStyleTests.py). Open the ordinary [rectangle and boss read](../../../src/convert/adapters/solidworks/resolved/RectanglePart.py) on `Contents/Config-0` and `Contents/Config-0-ResolvedFeatures`. In the unique boss `ReadDisplayOpen`, the cursor is at the first point after the style value has been read. Advance 148 bytes through the points and vectors to the first text byte. The offset on return from that call is the independently recovered `depth_display.handle.offset`.

## Following inline text and handle

The `moDisplayDim_c` caller resumes at `0x4c82a1e9` and calls serializer slot 5 on the inline `moDimText_c` member `+0x6a0` at `0x4c82a1f6`. The vtable at `0x4d243868` resolves that slot to `0x4c6e86b0`. Its plain saved text begins with the empty Unicode `iText` CString at member `+0x08`, written by the CString operator at `0x4c6e8870`. The next fields are the origin `Position` at `+0x38`, `FormatToUse` signed long 18 at `+0x10`, and the null `Format` object at `+0x18`. Their store calls are `0x4c6e88eb`, `0x4c6e892d` and `0x4c6e898c`. The constructor at `0x4c84ff90` initializes the points, a null format object on this path and scale 1.0. The `useOtherFormat` entry at `0x4c8578b0` writes the supplied format to `+0x10` and clears `+0x18`. The calling route that supplies 18 on this boss still needs attribution.

The 136 bytes from the empty CString through the last field before the handle also agree in all eight saves, with SHA-256 `f88940a3060281aebab6185f30814dc56f675b79047c28e1036dab141751cd6f`. The offset after them holds a compact schema-1 `moFeatureDimHandle_c` class definition. The typed walk reaches it at next map index 297, which allocates the handle class and object 298. The enclosing compact display reference has already allocated object 296 before `ReadDisplayOpen`, whose entry and exit both have next index 297. The `moDisplayDim_c` store writes `DimHandleCount` from `+0x860` at `0x4c82a35d` before the handle loop. Attribution of the remaining inline text fields and the producer of its selected format is needed before complete depth-display generation. [Handle and cache reader](../../../src/convert/adapters/solidworks/resolved/BossDepth.py)
