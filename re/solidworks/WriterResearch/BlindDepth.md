<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# A12 independent blind depth parameter record

[`EncodeDepth`](BlindDepth.py) emits the full named `moLengthParameter_c` child of an ordinary generation-19000 blind depth dimension. Its inputs are a symbolic parameter name, a positive depth in millimetres and the enclosing archive's allocations for the length and name classes. It emits only the compact class-reference forms witnessed in P03. The isolated probe exercised the existing [`SketchArchive.ReadObject`](../../../src/convert/adapters/solidworks/sketch/Cursor.py) reader. The enclosing display and end specification, the complete SLDPRT and native application acceptance remain pending. See the [portable boss mapping](PortableBoss.md).

## Field authority

| Field                                     | Construction                                                                                                                              | Evidence                                                                                                                                                                                                                                                                                                                                |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Length and name class references          | Emit one new `moLengthParameter_c` instance and its own new `moNodeName_c` instance from the caller's distinct compact class allocations. | The [archive tag codec](../../../src/convert/adapters/solidworks/container/Archive.py) and [typed map reader](../../../src/convert/adapters/solidworks/container/ArchiveTags.py) define the class-reference token and one-slot object allocation.                                                                                       |
| Node name and label                       | Encode the supplied parameter name and a separate empty label for this unlabelled depth node.                                             | [Length reader](../../../src/convert/adapters/solidworks/sketch/Objects.py). All three controls owned the name `depth_mm` and an empty label.                                                                                                                                                                                           |
| Inherited node words                      | Encode clean saved update state `0`, the document-ID allocation bit `0x40000000`, unset DocID `-1`, and clear secondary flags `0`.        | The generation-19000 serializer at `0x4c1789e0` owns the words. The `moNode_c` constructor at `0x4c03a5c0` seeds DocID `-1` and the allocation bit with clear secondary flags. Named update-state accessors at `0x4c03c8e0`–`0x4c03c920` and the three controls distinguish saved clean state from the constructor's initial state `1`. |
| Optional base pointer and length override | Emit a null base pointer and the zero override indicator for an ordinary local value.                                                     | The [parameter grammar](../records/Serialize.md) describes the optional alternate value. Modern evidence traces `0x4c175bd0` to the parameter base at `0x4c177f20`; the P03 controls all take the null and no-override branches.                                                                                                        |
| `Value`                                   | Write the explicit little-endian `float64` depth divided by 1000.                                                                         | The [length reader](../../../src/convert/adapters/solidworks/sketch/Objects.py) binds this value to the allocated parameter object. The [parameter grammar](../records/Serialize.md) independently identifies its native unit as metres and places reversal in the end specification.                                                   |

Modern addresses refer to `sldmodu.dll` build `34.4.1.1011`, SHA-256 `2201734ebe0106efde5a93e306067b4b5e2fdb0ba70bf38ce9a59242b283cb99`. No source byte range, offset, vendor template or saved class index is an input to independent emission.

## Independent emission and readback

The probe emitted both records with the symbolic name `DepthΩ` and synthetic class allocations `23` for length and `61` for name. With the next free slot at `79`, the existing typed reader allocated parameter object `79` and name object `80`, then advanced to `81`. It reached the end of each 51-byte record. The compared outputs matched outside the authored scalar at half-open offsets `[42, 50)`.

| Requested depth | Readback  | Emitted SHA-256                                                    |
| --------------- | --------- | ------------------------------------------------------------------ |
| 7.25 mm         | 0.00725 m | `b933528be7c6c7329d5f7b96e5a402f6098dfb585812f3dd4ea6df629c8469bd` |
| 18.5 mm         | 0.0185 m  | `24d24af82f0c5ab33532f4322527771345a70a2cf9972e73c44e47aebb48fb58` |

Re-emitting the 7.25 mm parameter with class allocations `117` and `42` and a next-free slot of `202` gave parameter object `202`, name object `203` and next-free slot `204`, with the same decoded name and length. These namespaces were supplied independently of the capture files.

To reproduce the readback from the worktree root, run this snippet with the locked Python environment.

```python
from hashlib import sha256
from sys import path

path[:0] = ["src", "re/solidworks/WriterResearch"]
from BlindDepth import EncodeDepth
from convert.adapters.solidworks.container.ArchiveCursor import ArchiveCursor
from convert.adapters.solidworks.sketch.Cursor import SketchArchive

classes = {23: "moLengthParameter_c", 61: "moNodeName_c"}
indexes = {name: index for index, name in classes.items()}
for depth in (7.25, 18.5):
    data = EncodeDepth("DepthΩ", depth, indexes)
    cursor = SketchArchive(ArchiveCursor(data, 0, 79, classes.copy(), {}))
    owner = cursor.ReadObject("moLengthParameter_c")
    print(owner, cursor.Scalars[owner], cursor.Offset, cursor.NextIndex)
    print(sha256(data).hexdigest())
```

## Saved controls and next boundary

The [P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json) pins the three source-file hashes. For the comparison only, the probe used the corresponding typed `ReadRectPart` dimension location and the archive's established class indexes. It derived the parameter from the recipe input and compared the resulting 55 bytes to the saved child. The typed display reader also recovered each corresponding pair of cached values. Offsets below are half-open within decompressed `Contents/Config-0-ResolvedFeatures`.

| P03 discovery variant | Depth and display copies (m) | Byte-identical parameter span | Resolved stream SHA-256                                            |
| --------------------- | ---------------------------- | ----------------------------- | ------------------------------------------------------------------ |
| `baseline-a`          | `0.01`, `(0.01, 0.01)`       | `[13820, 13875)`              | `3ca4fba98bfa49213e53ee463bfd59a03e589d2ecc7253ab699bd7f21748ab72` |
| `edit-width_mm-41`    | `0.01`, `(0.01, 0.01)`       | `[14048, 14103)`              | `652d18fc726ce6e2ecbd60bf6eb595a6fa226b0ae9cf2c4e362bc00c68186689` |
| `edit-depth_mm-12`    | `0.012`, `(0.012, 0.012)`    | `[14048, 14103)`              | `1fac5addf426e3041a62bd1dd90c49a36f8c2dd3fb6f259af8371120fbf03958` |

The parameter experiment stopped at the opening style fields in [`ReadDisplayOpen`](../../../src/convert/adapters/solidworks/sketch/DisplayOpen.py). The subsequent [display-style analysis](DisplayStyle.md) attributes all 94 bytes of `StyleValue` to the inherited native serializer and constructor for the measured empty branch. A constructed display and its placement, appearance edits and populated child records remain open. [Depth display reader](../../../src/convert/adapters/solidworks/resolved/BossDepth.py)

The typed boss-depth read reached the same 94-byte span in all eight receipt-pinned saves. Baseline A starts at `13273`. Baseline B, the three dimensional edits and the inch variant start at `13501`. The YZ-plane and negative-direction variants start at `13343` and `13271`, respectively. Each span has SHA-256 `5a3b29f9eea808f1984c8526c7474be07bc63b265894d6078c23860aeec1abc1`. [P03 receipt](../../automation/PairedCaptures/P03/solidworks-db1390476325/receipt.json)
