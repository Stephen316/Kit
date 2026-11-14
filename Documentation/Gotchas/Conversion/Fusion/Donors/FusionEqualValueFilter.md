# A filter for values equal across controls keeps design geometry

## Expectation

A default generator that keeps only values that are equal in all controls keeps only format defaults.
Values that change from one document to another drop out.

## Actual behavior

The drawing sheet defaults kept a circle with centre (-9780, -9841.5) and radius 3.999999999999999.
They also kept an entry count of 4 in the sort table.
Every control was a drawing of the same design, so the design geometry was equal in all of them.
The filter could not tell geometry from format defaults.
The placement code merged these defaults without a warning, so a missing field took the captured value.

## Workaround

Make the controls from unrelated designs, sizes and view sets before you filter.
Keep only schema type defaults and proven constants in a defaults file.
Make every geometric field from the placement input.
Fail when a placement leaves a geometric field unset.
Do not fill it from a default.
See the [donor data ban](../../../../Reference/Research/FusionDonorBan.md).
