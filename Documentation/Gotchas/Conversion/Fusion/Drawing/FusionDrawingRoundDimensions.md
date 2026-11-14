# Fusion's round dimensions differ from its linear ones

Fusion 2706.1.17 saved six vertical, six aligned, two radius and one diameter dimension in one drawing.
The [CaptureEdit2 evidence](../../../../../re/Fusion/Reconstruction/Drawings/Rules/CaptureEdit2.json) lists them.

| Property            | Vertical and aligned | Radius                  | Diameter        |
| ------------------- | -------------------- | ----------------------- | --------------- |
| Dimension flags     | 11                   | 10                      | 10              |
| Style overrides     | DIMLFAC only         | DIMLFAC, DIMSE1, DIMUPT | DIMLFAC, DIMUPT |
| Text prefix         | None                 | `R`                     | `∅` (U+2205)    |

The lowest bit of the flags says the text sits where the dimension style puts it.
Fusion clears it for round dimensions and sets DIMUPT, because the user places their text.

Fusion writes the diameter sign as U+2205, the empty set sign.
It measures the sign with the box of Arial's `Ø` (U+00D8).
`∅5` is 6.129 mm wide at 3.5 mm, the width of `Ø5`.

Kit writes the same flags, overrides and sign.
Kit's text extents come from Arial's glyph boxes and match all fifteen saved texts to 4 × 10⁻⁷ mm.

Fusion draws its round dimensions with the text on the radial line.
Kit draws the text on a shelf at the end of a leader, which ISO 129 also allows.
