# A referenced pcurve form selects and orients an intcurve pcurve

## Expectation

A `pcurve` record with a nonzero `Form` holds its own parameter curve, like a form 0 record.

## Actual behavior

A form of -2, -1, 1 or 2 holds no curve. `CurveRef` names an `intcurve-curve` record, and the form selects one parameter curve of that record. The parameter curves are the 2D B-spline blocks of the intcurve subtype, in stream order.

| Form | Parameter curve | Direction |
| --- | --- | --- |
| 1 | First | Same as the intcurve |
| -1 | First | Reversed |
| 2 | Second | Same as the intcurve |
| -2 | Second | Reversed |

The record itself is never reversed. The sign carries the sense instead. In the 116 complex corpus members, 372 coedges use a referenced form. A positive form occurs only on a forward coedge, and a negative form only on a reversed coedge.

Fusion 2706.1.17 reports the coedge geometry as the selected curve, reversed for a negative form, plus `OffsetU` and `OffsetV`. A refined parameter curve showed this in both directions.

| Case | Edited record | Coedges checked | Result |
| --- | --- | --- | --- |
| `PcurveFormRefine` | `par_int_cur`, first parameter curve, one knot inserted | Form 1 with no offset, form -1 with `OffsetU` -2π | Both coedges reported the 3 predicted poles |
| `TolerantFormRefine` | `int_int_cur`, second parameter curve, one knot inserted | Form 2 | Same curve, other representation, see the [refined pcurve knots gotcha](RefinedPcurveKnots.md) |

## Workaround

Read a referenced form through its sign and its index. Do not change the sign of a form without the coedge sense. `ReadGeometry`, `ReadJournal` and both emitters raise `ValueError` with `Fusion pcurve form sign disagrees with its coedge sense` for such a record.

A run before this check existed queued a body with one form changed from 1 to -1. Fusion exited during that run, and that body was the next case after the last checkpoint. The exact step is not known. No consistent input repeated the exit, and the body was not sent again.

## Evidence

- [Subtypes run](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Subtypes.json)
- [Preparation with the predicted poles](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Preparation.json)
- [Run with the Fusion exit](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Crashed.json)
- [Pcurve sense](PcurveSense.md)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
