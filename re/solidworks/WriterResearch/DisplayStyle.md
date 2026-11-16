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
