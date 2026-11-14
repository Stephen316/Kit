# Text metrics fitted from one string fail for other text

## Expectation

The extent of a dimension text in a Fusion drawing is a fixed ratio of the text height.
One measured text gives that ratio.

## Actual behavior

The drawing writer fitted its extent and digit ratios from the single text "40".
A third ratio, for the dimension mark, was an assumption.
Other digits, other fonts and text with a decimal point or a unit have other extents.
The fitted ratios give wrong extents for that text.

## Workaround

Compute text extents from the font metrics of each glyph.
Alternatively, test in local Fusion whether Fusion computes the extents again when it updates the drawing.
If it does, write no extents.
Validate with texts that the fit did not use.
See the [donor data ban](../../../../Reference/Research/FusionDonorBan.md).
