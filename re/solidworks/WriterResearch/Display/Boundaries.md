# Ordinary blind boss display opening and ownership

The exact eight P03 archives from save receipt SHA-256 `f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94` were walked with the packaged rectangle/boss reader. The receipt also pins the native measurement digest used to reconstruct the geometry. Baseline A, baseline B, depth/width/height edits, inch units, YZ support and negative direction all follow the same display record structure. The read-only replay checked each file's byte count and SHA-256. [Pinned receipt](../../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json), [source reader](../../../../src/convert/adapters/solidworks/Resolved/BossDepth.py)

## Opening before appearance

The 178 bytes immediately following the compact display class reference are identical in all eight saves. The SHA-256 is `33b382db285e0b9e004a5ceec0cfc9d0af2730f519bb0dcc7a4d3dd25c33ab63`. Offsets below are relative to the first byte after the class reference. Preferred virtual addresses belong to installed SOLIDWORKS 34.4.1.1011 `sldmodu.dll` SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`.

| Relative range | Typed shape and native owner |
| --- | --- |
| +0–8 | A clear `u16` at `0x4ba4c79d` and the three compact absent references written at `0x4ba4c91f`, `0x4ba4c951` and `0x4ba4c95d`. Constructor `0x4be74cfd–0x4be74d0d` clears the corresponding reference state. |
| +8–33 | Two signed longs written at `0x4ba4c969` and `0x4ba4c978`, then the inherited visual fields called at `0x4ba4c985`. The `0x4c14ef20` helper writes two `u16` members and one byte. `0x4c14f020` follows with the unsigned color, `u16` member and line width. Constructor `0x4be74cf7` supplies the inherited color and calls the visual initializer with the default line width. |
| +33–51 | Two empty compact inline reference-list counts from `0x4ba4ca50` and `0x4ba4ca60`, display index zero at `0x4ba4cb09`, and an empty `moLinkedDispObjArray_c` pointer at `0x4ba4cb19`. The associated presence word and current generation are stored at `0x4ba4cbdb` and `0x4ba4cc36`. The constructor initializes the empty lists and zero index at `0x4be74d11–0x4be74d9f` and obtains the archive generation at `0x4be74dbb–0x4be74dc7`. |
| +51–93 | Two signed model words at `0x4ba4b064` and `0x4ba4b074`, an origin and two empty signed presence words, followed by a null object pointer. The `moDisplayItem_c` constructor clears `+0x390` at `0x4ba64bd2` and builds the second word from `0x80` at `0x4ba64c13` and `0x80000` at `0x4ba64ded`. |
| +93–151 | The origin vector stored at `0x4ba4b0de` and identity transform stored at `0x4ba4b0ee`. The constructor calls the vector and transform initializers at `0x4ba64c81` and `0x4ba64a4f`. The latter serializes with an omitted basis, zero translation, unit scale and absent nested transform. |
| +151–178 | One map item stored from `0x4ba4b0fe` through `0x4ba4b126`, with the witnessed ordinary part display mode `201`. The inactive storage fields follow at `0x4ba4b194`, `0x4ba4b1bb`, `0x4ba4b1d4` and `0x4ba4b1f9`. The null child at `0x4ba4b244` ends the opening immediately before the first appearance double. |

## Complete display and enclosing return

Offsets in this table include the two-byte display class reference. The next object index is 296 at the display entry. The existing display, length, parameter-name and favorite classes must already be present in the caller's map.

| Relative range | Owner |
| --- | --- |
| +0–180 | Display class reference and opening. The class reference creates display object 296. |
| +180–558 | Appearance, points, vectors, inline text and one-handle count. |
| +558–691 | Feature dimension handle class 297 and object 298. |
| +691–1037 | Parallel distance class 299 and object 300, length parameter 301 and name object 302. |
| +1037–1277 | Enclosing display placement. The caller supplies its annotation witness projection. |
| +1277–1369 | Two copies of the positive model depth and the fresh cache flags. |
| +1369–1383 | Favorite object's existing class reference creates object 303. |
| +1383–1753 | Base return including ignored transform padding and the normalized inactive `SelLeader`. |
| +1753–1807 | Distance subclass return. The next map index is 304. |

The production `ReadBossClose` next enters `ReadEndTail`, starting with a null object. The `moFromEndSpec_c` definition occurs at display end +76 and allocates class 304 and object 305. It owns one signed sketch-plane type word at +97–101. Its parent `moEndSpec_c` owns the five signed longs at +101–121. The installed reader sequence already identifies these as `CapEnd[0]`, `CapEnd[1]`, `DelInitFace`, `KnitRes` and `CreateSolidFrmCappedMidPlaneSurfExt`. The eight raw P03 rows are `(0xe90ccff2, 0, 0x45877cf9, 0x0c5e87e0, 0)` in six Front controls, `(0xe90ccff2, 0, 0x45877cf9, 0x06ed9df0, 0)` in YZ, and `(0xe90ccff2, 1, 0x45877cf9, 0x06ed9df0, 0)` in the negative Front control. Hexadecimal notation shows the exact 32-bit bit patterns. The variation records association in these saves. It gives no constructive rule equating the second word with reversal or the fourth with support. [Native owner field map](../../records/Serialize.md), [earlier independent tail attribution](../../records/VersionedRuns.md#63-mofromendspec_c--type-zero-and-its-enclosing-tails-are-closed)

`ReadBossClose` then consumes +12 bytes before the extrusion returns. `ReadRectBoss` consumes a four-byte list footer and reaches the end of each decompressed stream. The display constructor stops before these parent fields and keeps their saved words outside its inputs. [Enclosing owner reader](../../../../src/convert/adapters/solidworks/Resolved/BossEnd.py), [display composition](Compose.py), [base return evidence](../DisplayBaseFields.md)
