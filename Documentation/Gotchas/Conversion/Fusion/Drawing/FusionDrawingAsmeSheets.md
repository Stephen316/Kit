# Fusion's ASME sheets need an ASME drawing

Fusion 2706.1.17 sets the drawing standard only when it creates a drawing.
`CreateDrawingInput.standard` takes it, and `DocumentSettings.standard` is read-only.
Setting an ASME sheet size on a sheet of an ISO drawing fails with "Sheet size is not valid for the active drawing standard".

Every ISO save Kit has holds the ten ISO border blocks and an `ANSI_TITLEBLOCK` block.
None holds an ASME border block, so Kit cannot read Fusion's ASME border from an ISO save.

Fusion's sheet size page gives the ASME sizes in inches.
Kit's standard objects use millimetres, so Kit writes an ASME sheet in millimetres: B is 431.8 × 279.4 mm.

Kit's ASME border follows the ASME sheet family, not a Fusion template:

* 0.5 in margins on every side and no filing margin.
* Each zone is a quarter of an A sheet.
  Each zone is 4.25 in along a side from the 8.5 in side and 5.5 in along a side from the 11 in side.
  A has 2 × 2 zones, B 4 × 2, C 4 × 4, D 8 × 4 and E 8 × 8.
* The zones span the whole sheet, so the outer zones take the margins.
* Numbers count from the right and letters from the bottom, so zone A1 is the lower right corner.
* Labels are 0.12 in high and sit in a 0.25 in band outside the frame.
* No trim marks and no centring marks.

Fusion opened the A3 control with Kit's B, D and A borders and layouts grafted in, as the [T7 report](../../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT7.json) records.
It read each sheet size from the DWG layout.
This shows Fusion accepts the sheets, not that they match Fusion's own ASME template.
