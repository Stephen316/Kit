# Fusion's template borders do not follow one rule

Every Fusion 2706.1.17 drawing keeps ten border blocks from its template.
They are `ISO_A0_SHEET` to `ISO_A3_SHEET`, the same four with `(P)` for portrait, and `ISO_A4(L)_SHEET` and `ISO_A4(P)_SHEET`.
Only the block of the current sheet is inserted.

Kit's border rule follows ISO 5457.
It has a 20 mm filing margin, 10 mm on the other sides, and 2·round(side/100) zones per side.
Those counts are the ISO 5457 field table: 24 × 16 for A0 down to 6 × 4 for A4.
The zone pitch is the band span divided by the zone count.
The band span is the frame span plus 5 mm on each side.

| Fusion block            | Fusion's geometry                                   | Kit compared        |
| ----------------------- | --------------------------------------------------- | ------------------- |
| A0 to A3 landscape      | Band span divided by the zone count                 | Same to 2 × 10⁻⁴ mm |
| A0, A2 and A3 portrait  | Frame span divided by the zone count; MTEXT labels  | Different pitch     |
| A4 landscape and portrait | No zones; portrait has no bottom centring mark   | Kit draws 6 × 4 zones |
| A4 landscape            | Side centring marks at y = 100 mm, frame centre 105 mm | Kit centres them |

The landscape and portrait templates divide different spans, so no single rule gives both.
The A4 side marks are off the frame centre.
These are properties of Fusion's template drawings, not of the DWG format.
Fusion opened a graft with Kit's border block in place of its own.
[GraftRoundT4.json](../../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT4.json) records it.

Kit keeps one ISO 5457 rule for every sheet.
It fits the A3 landscape block and matches the other landscape blocks it was not fitted on.
