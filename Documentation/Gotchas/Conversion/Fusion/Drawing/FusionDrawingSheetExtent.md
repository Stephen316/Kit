# Fusion takes the drawing sheet extent from the DWG layout

## Expectation

A Fusion drawing stores its sheet in the drawing members: `sheetWidth`, `sheetHeight`,
`sheetSize`, `standard` and `units` in the sheet member that
[`SheetCodec`](../../../../src/convert/formats/Fusion/DrawingCodec/Members/SheetCodec.py) reads and
writes. Changing those values should change the sheet.

## Actual behavior

Fusion 2706.1.17 ignores the member and uses the `LAYOUT` object inside the embedded DWG.

A control changed only the member, from A3 to A1, and left the DWG byte-identical.
Fusion opened the drawing and still reported the A3 extent:

```
member written   A1 Landscape 841.0 x 594.0
DWG database     unchanged
Fusion reported  sheet_mm [420.0, 297.0]   views [5, 4, 4]   dimensions 1
```

A second control changed only the `LAYOUT` object, from `420.0 x 297.0` with
`ISO_full_bleed_A3_(420.00_x_297.00_MM)` to `841.0 x 594.0` with
`ISO_full_bleed_A1_(841.00_x_594.00_MM)`, and left the members alone.
Fusion reported the new extent:

```
layout written   841.0 x 594.0  ISO_full_bleed_A1_(841.00_x_594.00_MM)
Fusion reported  sheet_mm [841.0, 594.0]   views [5, 4, 4]   dimensions 1
open             4.9 s
```

## The sheet name does not follow the member either

A third control changed only the member's `ActiveSheet` from `KitDrw Source 20261112114717` to
`Kit Sheet Renamed`, with the DWG byte-identical.
Fusion opened the drawing and reported the old name:

```
member written   Kit Sheet Renamed
DWG database     unchanged
Fusion reported  sheet name "KitDrw Source 20261112114717", 420.0 x 297.0, views [5, 4, 4]
open             5.8 s
```

The name Fusion shows is the source document name, not the member value.
The member is a mirror of the drawing, not the value Fusion reads.

## Workaround

Change the `LAYOUT` object and re-emit the DWG.
The layout carries `PaperWidth`, `PaperHeight` and `PaperSize`, and the paper name is the
`ISO_full_bleed_<size>_(<width>_x_<height>_MM)` form.
Keep the member in step so a reader that trusts the member sees the same extent.

The header tail is unaffected because the checksum covers the header area and not the layout objects,
so a layout edit keeps the document's own tail valid.

## Evidence

| Case              | Change                    | Fusion sheet_mm | Views     | Dimensions |
| ----------------- | ------------------------- | --------------- | --------- | ---------- |
| `C20SheetA1`      | member only, A3 to A1     | `[420.0, 297.0]` | `[5,4,4]` | 1          |
| `C21LayoutA1`     | `LAYOUT` only, A3 to A1   | `[841.0, 594.0]` | `[5,4,4]` | 1          |
| `C24SheetName`    | member name only          | `[420.0, 297.0]` | `[5,4,4]` | 1          |

Both cases come from `D1FreshLayout` and were opened in local Fusion 2706.1.17.
The builders are
[`BuildSheetNameCase.py`](../../../../re/Fusion/Reconstruction/Drawings/ThirdParty/BuildSheetNameCase.py)
and [`BuildLayoutCase.py`](../../../../re/Fusion/Reconstruction/Drawings/ThirdParty/BuildLayoutCase.py).

## Limits

The corpus holds 247 Fusion-saved drawings and every one is A3 Landscape, so the corpus alone cannot
tell a read value from a constant. These two controls change one input each, which is why they carry
the conclusion.
