# Knot intervals set the converted parameters but not the jump lists

## Expectation

A TSM edge knot interval only spaces the T-spline parameters. Fusion would store the same converted body for every interval, or Kit could derive the body from the unit body. Kit refused every interval other than 1.

## Actual behavior

Fusion 2706.1.17 imported and converted a 4 × 4 plane grid and the box primitive with other intervals. All 11 imports had Form health 0, and zero documents stayed open.

| Cage | Intervals | Converted knots | Kit result |
| --- | --- | --- | --- |
| Plane 4 × 4 | All 1 | 0, 1, 2, 3, 4 | Equal |
| Plane 4 × 4 | All 2 | 0, 2, 4, 6, 8 | Equal |
| Plane 4 × 4 | All 0.5 | 0, 0.5, 1, 1.5, 2 | Read; conversion refused |
| Plane 4 × 4 | Column 1 at 2 | U: 0, 1, 3, 4, 5 | Refused |
| Plane 4 × 4 | Column 0 at 2 | U: 0, 2, 3, 4, 5 | Refused |
| Plane 4 × 4 | Row 2 at 3 | V: 0, 1, 2, 5, 6 | Refused |
| Plane 4 × 4 | Column 1 at 2 and row 2 at 0.5 | V: 0, 1, 2, 2.5, 3.5 | Read; conversion refused |
| Plane 4 × 4 | One edge at 2 | U: 0, 1, 2.0588235294117645, … | Read; conversion refused |
| Box | All 1 | 0, 0.25, 0.5, 1, 1.5, 1.75, 2 | Equal |
| Box | All 2 | 0, 0.5, 1, 2, 3, 3.5, 4 | Equal |
| Box | One edge at 2 | 0, 0.2586206896551724, … | Read; conversion refused |

The knots are the running sums of the column and row intervals. The poles stay the grips, within 2.2e-15 cm of the unit conversion. Each patch cell and progenitor window spans its intervals. The patch program then holds values such as `0.5` and `-2.5`. Each word is an integer or a double written as `%.17g`. `PatchCell` keeps float windows and offsets, and its face index and turn stay integers.

An interval that differs from its grid row or column is inconsistent. Fusion rewrote such cages on import. It saved some intervals as 1.0588235294117645, moved grips and added `106ek` and `50000grip` TSM records. The `106ek` block has one record per edge, after the symmetry block and before the smart grips. In both saves each value equals that edge's knot interval. `ReadTspline` returns a `KnotSurface` that keeps the block in `EdgeKnots`, and `ConvertForm` refuses a cage whose records differ from the intervals.

The jump lists do not follow the parametric rule of the [discontinuity gotcha](ConvertedDiscontinuityLists.md). The plane is flat, so each boundary curve is a straight line. With mixed intervals, its third derivative jumps by 0.16 to 0.67 at interior knots. Each jump lies along the curve direction within 5.6e-17. Fusion stored empty lists. So Fusion does not record a jump along the tangent here. Its exact test is not confirmed by a black-box experiment.

## Workaround

`ConvertGrid` accepts one whole-number interval c from 1 to 4096 on every edge. It scales the knots, patch cells, pcurves and progenitor windows by c. It computes the jump lists on the unit-parameter surface and scales their knots by c. A uniform scale changes no geometry, so the verified unit rule still holds.

Fusion accepted two warped grids that `EmitFormDoc` wrote with intervals 2 and 3. Each Kit document equalled the Fusion conversion of its TSM within 2.7e-15 cm, and the jump lists were equal. Both documents passed the edit, save and reopen stages.

| Cage | Error |
| --- | --- |
| Grid with mixed intervals | `Fusion grid conversion needs one knot interval for every edge` |
| Grid with a fractional or larger interval | `Fusion grid conversion needs a whole-number knot interval` |
| Closed or creased cage with mixed intervals | `Fusion Form capped layout needs one shared knot interval` |
| Closed or creased cage with a fractional interval | `Fusion Form capped layout needs a whole knot interval` |

`CageBody` takes one whole-number interval c on every edge of a closed or creased cage. It converts the unit cage and scales every parameter by c. The box with every interval 2 equals Fusion within 1.0e-13 cm.

Mixed intervals need Fusion's own jump test, and no curved local archive tests it. Fractional intervals need non-integer cell bounds in the conversion.

## Evidence

- [Interval check](../../../../../re/Fusion/Reconstruction/FormDocuments/IntervalCheck.json)
- [Interval probe](../../../../../re/Fusion/LocalOracle/FormDocuments/Intervals/Probe.json)
- [Interval preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/Intervals/Preparation.json)
- [Interval document acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/IntervalDocuments/NativeAcceptance.json)
