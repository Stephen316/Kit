# Converted Form geometry stores third-derivative discontinuities

## Expectation

A converted Form face of an uncreased grid cage has smooth interior knots. Its six jump arrays and the discontinuity list of each boundary curve stay empty.

## Actual behavior

Fusion 2706.1.17 records each interior knot where the third derivative jumps. The surface stores these knots in its third jump array for each direction. Each `exact_int_cur` boundary curve stores them in its order-3 discontinuity list. A reversed boundary curve stores the negated knot values.

| Native body | Surface U list | Surface V list | Boundary curve lists |
| --- | --- | --- | --- |
| Plane primitive with 2 × 3 faces | Empty | Empty | Empty |
| The same plane after one vertex move | 1.0 | 1.0 and 2.0 | (), (), (−1.0) and (−2.0, −1.0) |
| Warped Kit cage after one vertex move | 1.0 | 1.0 and 2.0 | (1.0), (1.0, 2.0), (−1.0) and (−2.0, −1.0) |

Kit does not reproduce Fusion's exact tolerance rule. The census measured the largest third-derivative jump at each interior knot of 26 equal bodies that Fusion wrote.

| Knot class | Knots | Jump size |
| --- | --- | --- |
| Recorded by Fusion | 122 | At least 0.13 |
| Not recorded by Fusion | 118 | At most 3.3e-15 |

A writer that keeps stale lists writes a body that differs from the native conversion. The census marks two stale probe variants as different for this reason.

## Workaround

Compute the third-derivative jump at each interior knot of each surface row, column and boundary curve. Record a knot when a jump component exceeds 1e-10. `GridJumps` and `ThirdJumps` implement this rule. `JumpCurve` writes the list into the curve. Do not rely on this threshold for a jump between 1e-14 and 0.1, because no local body tests that range.

## General order rule

Converted box and prism faces have double knots at their G1 caps. Fusion records each interior knot in the list of the lowest derivative order that jumps there. A double knot usually lands in the order-2 list, and a simple knot in the order-3 list. A surface takes the lowest order over all its rows or columns.

| Archives | Form bodies | Surfaces | Curves | Different |
| --- | --- | --- | --- | --- |
| Committed local archives | 78 | 362 | 844 | 1 |
| Stencil probe outputs | 341 | 3927 | 8982 | 0 |

The different archive is the cache probe whose surface poles Kit moved without its lists. `SurfaceOrders` and `CurveOrders` in `OrderJumps` implement the rule with the same 1e-10 threshold. `OrderCurve` writes all three curve lists. `ConvertCage` uses them for every face and boundary curve.

## Evidence

- [Grid census with the jump margins](../../../../../re/Fusion/Reconstruction/FormDocuments/GridCensus.json)
- [Grid acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/Grid/NativeAcceptance.json)
- [Jump order census](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/JumpCensus.json)
- [Grid pole order](GridCagePoleOrder.md)
