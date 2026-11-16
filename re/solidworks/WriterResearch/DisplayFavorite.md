# Ordinary blind boss favorite and return

The generation-19000 part archive reaches a compact `moFavoriteHandle_c` class reference after the 92-byte display cache. The full closing span is 438 bytes on all eight pinned P03 captures. It contains the favorite occurrence at +0–14, the resumed `moDisplayDim_c` base at +14–384 and the enclosing `moDisplayDistanceDim_c` return at +384–438. The packaged `ReadDepthClose` consumes the whole span. The research codecs generate the first and last owners separately. [Display cache](DisplayCache.md), [packaged depth reader](../../../src/convert/adapters/solidworks/Resolved/BossDepth.py)

## Favorite handle

The source below is from installed SOLIDWORKS 34.4.1.1011, with `sldmodu.dll` SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99` and `sldmgu.dll` SHA-256 `3b82cfcaa13f099fca4f9741acbb11479dab7a6f20656052d5a750e61c6fee1e`. The addresses are preferred virtual addresses.

The ordinary display creates the favorite at `0x4c86d8cc`, calling `moFavoriteHandle_c(favorite_type, int)` at `0x4c8394c0` with type 0 and signed index −1. The constructor writes those fields to members `+0x8` and `+0xc`. It initializes the unsigned field at `+0x10` to zero. `getFavorite` at `0x4c839739–0x4c839740` returns absent for a negative index before looking up any favorite list. The display property `FavoriteName` from the preceding cache is separately empty. No favorite settings object is allocated by the handle.

The base writes the object pointer for member `+0x688` at `0x4c82b3ed`. The class's serializer slot 5 points to `0x4bb00e50`. Its store writes two signed longs at `0x4bb00e8f` and `0x4bb00e9b`, then one unsigned long at `0x4bb00ea7`. The modern read branch accepts that third field starting at generation `0x72d`. The ordinary captured payload is 12 bytes under the two-byte tag. This occurrence allocates one object under the earlier class definition. Reference index 221 and object index 303 come from the controls. The encoder uses the caller's archive map. The semantics of nonzero auxiliary values and the populated favorite settings route remain outside the codec. [Research favorite codec](DisplayFavorite.py)

## Enclosing distance return

The subclass serializer at `0x4c82ee40` first calls the base at `0x4c82ee6a`. It then writes the fields below. These fields use the ordinary feature-distance constructor at `0x4c8a25a0`. The bend initializer at `0x4b5949e0` clears both coordinates. The `mgPoint_c` constructor at `0x31de3a20` clears its three stored coordinates. The subclass clears the remaining returned members at `0x4c8a261b–0x4c8a2629`. [Research subclass codec](DisplayReturn.py)

| Offset from favorite tag | Field | Encoding and native store |
| --- | --- | --- |
| +384 | `DDMask` | Signed long 0, member `+0x1014`, store `0x4c82eeb6` |
| +388, +396 | `BentPts0` | Two zero doubles, members `+0xfb8` and `+0xfc0`, stores `0x4c82ef20` and `0x4c82ef31` |
| +404 | Stored point | Three zero doubles, member `+0xfe8`, point write operator at `0x4c82ef41` |
| +428 | `SelectedFirst` | Signed long 0, member `+0x1000`, store `0x4c82ef7d` |
| +432 | `ParentRadialDim` | Compact null object pointer, member `+0x1008`, binary object write at `0x4c82f014` with condition two clear |
| +434 | Trailing subclass state | Signed long 0, member `+0x1010`, store `0x4c82f039` before return |

## Intervening base fields

The observed middle includes alignment fields, `Mask2`, disabled override values, the identity `ForeShortDimXForm`, empty override text and multiple absent references. Native store sites include `Mask2` at `0x4c82b533` and `Mask3` at `0x4c82bc5f`. The exact controls save `0xe0e241fd` at +26 and `0x000f4a75` at +242. The base constructor's first values at `0x4c887f83` and `0x4c887f8d` are `0xfc` and `0x1870`. The ordinary constructor and document settings further mutate those masks. Deriving the final masks and the remaining settings from typed inputs still requires tracing those updates.

The legacy binary `mgXform_c` archive operator at `0x31f2d9a0` writes 30 unsigned longs from a temporary. Its stored layout includes nine rotation doubles, a matrix status word, an unwritten word, three translation doubles, scale, transform flags and a final clear word. The unwritten word at transform +76 is +156 from the favorite tag. All eight archives contain 32763 there. The store prepares matrix status at `0x31f2da05` and resumes with translation at `0x31f2da0c`, leaving that word unwritten. The binary loader at `0x31f30fa0` reads the 30 longs before constructing the matrix at `0x31f3106d`. That constructor copies only the nine doubles and recomputes matrix status. Translation starts at +80. The observed padding value is outside the interpreted fields. [Legacy transform padding](../../../Documentation/Gotchas/Conversion/SolidWorks/LegacyDisplayTransformPadding.md)

## Pinned archive verification

The receipt SHA-256 `f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94` binds all eight native saves and separate measurements. Every read-only replay followed the actual cache boundary into class 221 and produced exactly object 303 before returning to the operation at object-map index 304. The full 438-byte span is identical across the eight archives with SHA-256 `ce2794a2afdb423d77abef3f8224d249f75208c75dbd762e13701510a9003c4b`. The 14-byte favorite span SHA-256 is `7e875e25d20e483dfbdda1eeaf9f195d8818e20ed3a27cbad700a264351c2c03` and the 54-byte subclass span SHA-256 is `ea659cdc838619b3767c057fdf8e6d99fde2680c5d8517eb06761c0878d40c40`. [Pinned receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)

| Controls | Favorite tag through returning operation cursor |
| --- | --- |
| Baseline A | 14462–14900 |
| Baseline B, width, height and depth edits, inch display | 14690–15128 |
| Right plane | 14532–14970 |
| Negative direction | 14460–14898 |

The hosted archive path compares both generated fragments to the pinned intervals and separately uses the packaged reader to verify the complete native close from the original file. Hosted execution for these two fragments is pending. Completing the intervening base display fields, assembling the full operation and performing licensed native acceptance remain open. [Hosted archive verification](../../../tests/Research/Archives/SolidWorksCloseVerify.py)
