# Negative extent direction negates the distance expression

## Expectation

A one-side extrude created with `NegativeExtentDirection` keeps a positive distance parameter.
The direction is stored separately, so a new positive value keeps the same direction.

## Actual behavior

Fusion 2706.1.17 stores the direction in the distance expression.
A 4 mm cut created with `NegativeExtentDirection` has the expression `-( 4 mm )`.
Setting that parameter's expression to `5 mm` reverses the cut.
The cut then points away from the body and removes nothing.

The first P04 capture showed this.
Its `cut_depth_mm` = 5 edit measured 8000 mm³, which is the uncut block, instead of 7600 mm³.

## Workaround

Edit a Fusion distance parameter by replacing only the number in its existing expression.
For example, change `-( 4 mm )` to `-( 5 mm )`.
Record the stored expression with each capture, because the sign is part of the native semantics.
The [shared capture code](../../../../../re/automation/PairedCaptures/FusionCapture.py) does this.
A reader must not treat a negative distance expression as an invalid depth.
