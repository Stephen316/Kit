# Blind boss display style ownership

The 94-byte appearance span reached by [`ReadDisplayOpen`](../../../src/convert/adapters/solidworks/Sketch/DisplayOpen.py) in eight receipt-pinned P03 saves comes from the inherited `moDisplayItem_c` serializer. The ordered member writes identify the leading 74 bytes, and the five following signed words finish at the start of the four saved points. All addresses below are preferred virtual addresses in installed SOLIDWORKS 34.4.1.1011.

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

To reproduce the offsets, verify the receipt, measurement digest, file sizes and file digests as in the [hosted archive check](../../../tests/Research/Archives/SolidWorksBossStyleTests.py). Open the ordinary [rectangle and boss read](../../../src/convert/adapters/solidworks/Resolved/RectanglePart.py) on `Contents/Config-0` and `Contents/Config-0-ResolvedFeatures`. In the unique boss `ReadDisplayOpen`, the cursor is at the first point after the style value has been read. Advance 148 bytes through the points and vectors to the first text byte. The offset on return from that call is the independently recovered `depth_display.handle.offset`.

## Inline dimension text

The three exported `moDisplayDistanceDim_c` constructors at `0x4c8a2230`, `0x4c8a2350` and `0x4c8a25a0` install vtable `0x4d2501a0` before calling `0x4c8871e0` at `0x4c8a22bd`, `0x4c8a23f0` and `0x4c8a264a`. The common initialization helper calls display vtable slot `+0xae0` at `0x4c887233`. That entry is `0x4bc4bf10` and returns 18. The helper passes that result to slot `+0xa8` of the inline `moDimText_c` at display member `+0x6a0`, at `0x4c887242`. The inline vtable `0x4d243868` resolves this to `useOtherFormat` at `0x4c8578b0`, which writes the selector to `+0x10` and clears the explicit format object at `+0x18`. The base display table `0x4d24e738` has a different selector target returning 2, so the saved value 18 follows the distance-display class dispatch.

The base constructor overloads call `moDimText_c` at `0x4c84ff90` with an empty label, absent format and position inputs, zero flag arguments, width and height from the two `1e-6` values at `0x4cd973d0`, and width factor from `1.0` at `0x4cd973c0`. The calls at `0x4c86c439`, `0x4c86cc28` and `0x4c86d397` pass these same values. The inline constructor initializes the two points at `0x4c84fffe` and `0x4c850009`, sets scale 1.0 at `0x4c85001a`, clears the curve and mirror members, and constructs the empty `su_CStringArray` at `0x4c85009d`. Its later scalar stores at `0x4c85006e` through `0x4c8500dd` populate the supplied text box and font settings.

After the terminal display item vectors, `moDisplayDim_c` calls serializer slot 5 on the inline text member at `0x4c82a1f6`. Its vtable resolves that slot to `0x4c6e86b0`. The inherited `su_CObject::Serialize` call at `0x4c6e8712` contributes no bytes on the plain route and the subsequent database-key calls do not add fields there. The saved order below uses offsets relative to the first CString byte. The last row belongs to the outer display and is shown to make the next object boundary explicit.

| Offset | Member or native key | Wire type | Saved value | Store call |
| ---: | --- | --- | --- | --- |
| 0 | `+0x08` `iText` | Unicode CString | empty, four-byte framing | `0x4c6e8870` |
| 4 | `+0x38` `Position` | `3 f64` | `(0, 0, 0)` | `0x4c6e88eb` |
| 28 | `+0x10` `FormatToUse` | `i32` | 18 | `0x4c6e892d` |
| 32 | `+0x18` `Format` | archive object | compact null | `0x4c6e898c` |
| 34 | `+0x20` `AlignType` | `i32` | 0 | `0x4c6e89ea` |
| 38 | `+0x50` `EndPoint` | `3 f64` | `(0, 0, 0)` | `0x4c6e8a65` |
| 62 | `+0x68` `Scale` | `f64` | 1.0 | `0x4c6e8aa9` |
| 70 | `+0x90` array count | `i32` | 0 | `0x4c6e8ad7` |
| 74 | `+0xc4` `MirrorHorizontal` | `i32` | 0 | `0x4c6e8e3b` |
| 78 | `+0xa0` `CurveText` | `i32` | 0 | `0x4c6e8e9c` |
| 82 | `+0xd0` `TextInBoxStyle` | `i32` | 0 | `0x4c6e9383` |
| 86 | `+0xd8` `TextInBoxWidth` | `f64` | `1e-6` | `0x4c6e93e6` |
| 94 | `+0xe0` `TextInBoxHeight` | `f64` | `1e-6` | `0x4c6e9449` |
| 102 | `+0x24` | `i32` | 0 | `0x4c6e94a7` |
| 106 | `+0xf0` `TextInBoxSplitData` | compact count | 0 | `0x4c6e9509` |
| 108 | `+0x118` `TextInBoxSplitDataReady` | `i32` | 0 | `0x4c6e955a` |
| 112 | `+0x120` `IsUserOverridenText` | `i32` | 0 | `0x4c6e95bb` |
| 116 | `+0x124` `IsFitText` | `i32` | 0 | `0x4c6e961c` |
| 120 | `+0x128` `WidthFactorBeforeFit` | `f64` | 1.0 | `0x4c6e967f` |
| 128 | `+0x130` `WasUsingTableOrDocFontBeforeFit` | `i32` | 0 | `0x4c6e96e0` |
| 132 | outer display `+0x860` `DimHandleCount` | `i32` | 1 | `0x4c82a35d` |

The first empty count skips the array stores starting at `0x4c6e8b10`. The clear curve selector jumps from `0x4c6e8ec5` to `0x4c6e9344`, bypassing its additional geometry. The format-pointer helper in the pinned `sldmfcu.dll` routes through `su_CArchive::WriteObject` at `0x3c7cf68e`. At offset 106, `swccu.dll` SHA-256 `7254b30f4eb77fd5b49fdbb0a7ab499ba3bf1d39a3f8f18d72090c2568967b49` delegates the plain `su_CStringArray::Serialize` route at `0x31a476f4` to MFC ordinal 12836. In the inspected `mfc140u.dll` SHA-256 `fc5848eb58982e193cdfe73f1f26cd04fce4e196f717f42b89ae27315cd52f6f`, the array constructor reached through ordinal 962 clears its count at `0x1801d4da8`. The serializer reads it from `+0x10` at `0x1801d54fb`, and the count writer at `0x1801d1ea4` uses a 16-bit word for values below `0xffff`. The eight archives independently show a two-byte zero count there. The `+0x24` word is the second half of the qword cleared at `0x4c84ffe9`. Its meaning remains unassigned because the same database key is also used for the preceding height.

All eight saved inline text spans are 132 bytes with SHA-256 `eaed804b70c0f2af5875c9df36b4eb2c48108d3004d09c81c9cc2c386c914930`. Adding the outer one-handle count yields 136 bytes with SHA-256 `f88940a3060281aebab6185f30814dc56f675b79047c28e1036dab141751cd6f`. `ReadDisplayOpen` consumes the inline text and count with the same next map index 297 it had on entry after display object 296. The edited depth changes the actual model value to 0.012 metres while preserving the text bytes.

## First feature handle and owned dimension

For the plain archive the display stores handles from its array at `+0x858` via the object operator at `0x4c82a401`. The model-writing constructor route at `0x4c86d2b0` creates the supplied runtime-class dimension through `0x4c81ea90` at `0x4c86d7f3`, wraps that result using the initializer at `0x4c839f80`, installs the feature-handle vtable `0x4d1881b0`, and adds it to the display handle array at `0x4c86d848`. Its serializer slot 5 is `0x4c832420`. That calls the reference-dimension serializer `0x4c828570` at `0x4c832432`, whose component reference begins at `0x4bba6160`. The reference serializer stores the optional transforms, view tags and route fields before returning. The feature serializer's plain store path writes the object from `+0xf0` at `0x4c832545` when the `+0xe8` route is absent. This is the next typed dimension boundary in the saved record.

The [production boss reader](../../../src/convert/adapters/solidworks/Resolved/BossDepth.py) observes the same 133-byte span in all eight archives from the `moFeatureDimHandle_c` definition to the start of `ParallelPlaneDistanceDim_c`. Its SHA-256 is `13282cefe47002dea925f0081a4341fb4210ab2c373696857a4d09095efce523`. The 26-byte compact schema-1 definition allocates class 297 and object 298. The following null and 20 signed component words consume 82 bytes. The remaining 25 bytes match the [shared local dimension route](../../../src/convert/adapters/solidworks/Sketch/DimHandle.py) with selector 0, state -1, flags 0 and absent transforms. The typed dimension definition begins exactly at handle offset plus 133 and allocates class 299 and object 300. These indices are observed positions in the pinned inputs. A constructive writer must derive them from its own enclosing archive's allocation state.

The [handle component and owned dimension evidence](DisplayHandle.md) accounts for the handle defaults and distinguishes the dimension's true end from the following display fields. The favorite tail and application acceptance of an independently authored feature remain open.
