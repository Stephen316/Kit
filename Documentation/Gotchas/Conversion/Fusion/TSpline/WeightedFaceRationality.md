# Weighted grips make only their own faces rational

## Expectation

A cage with one weighted grip converts to a rational body. Every converted face and curve then stores weights.

## Actual behavior

Fusion 2706.1.17 stores a face or curve as rational only when one of its poles depends on a weighted grip. The other faces and curves keep the non-rational form. A rational face stores the `nurbs` keyword and the form `both`. Each pole holds the Cartesian point and its weight.

The TSM grip coordinates are homogeneous. A pole of the conversion is therefore the stencil row applied to the homogeneous grips, divided by the row applied to the weights.

| Value | Rule |
| --- | --- |
| Pole weight | The sum of c · w over the stencil row |
| Pole point | The sum of c · (x · w) over the row, divided by the pole weight |
| Rational entity | Any row of the face or curve uses a grip whose weight differs from 1 by more than 2^-51 |
| Discontinuity lists | The jump rule applied to the homogeneous poles |

Fusion edits can leave a weight at 1.0000000000000002. Such a cage still converts to non-rational faces and curves. The 2^-51 slack covers this case.

`WeightCheck.py` converted the stored cage of eight Fusion-saved archives with `ConvertCage`. It compared every face, curve, form flag and jump list with the body that Fusion stored.

| Archives | Weights | Rational faces | Rational curves | Largest point gap (cm) | Differences |
| --- | --- | --- | --- | --- | --- |
| Box with weight 2 on every grip | 2 | 6 of 6 | 12 of 12 | 1.6e-15 | 0 |
| Six box variants with grip 0 at weight 2 | 1 and 2 | 6 of 6 | 9 of 12 | 4.4e-15 | 0 |
| Creased plane edited by Fusion | 1 and 1.0000000000000002 | 0 of 2 | 0 of 7 | 4.4e-16 | 0 |

The pole weights agreed within 3.8e-15 in every archive.

## Workaround

`EvaluateRows` in `StencilRows` evaluates each stencil row on the homogeneous grips. `ConvertCage` writes a rational surface or curve only for a weighted row. An unweighted entity keeps the exact unit path. `SurfaceOrders` and `CurveOrders` compute the jumps on the homogeneous poles. `ConvertGrid` still refuses weights, because no weighted grid conversion exists locally.

## Evidence

- [Weight check](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/WeightCheck.json)
- [Weight probe](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/WeightProbe.json)
- [Weighted grip coordinates](WeightedGripCoordinates.md)
