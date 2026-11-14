# ASM and the Fusion API list surface poles in different orders

## Expectation

A B-spline surface lists its control points in one order. The order in the ASM stream and in `NurbsSurface.getData` looks the same.

## Actual behavior

The ASM `exact_spl_sur` block stores V rows. The U index changes fastest inside each row. `NurbsSurface.getData` in Fusion 2706.1.17 returns the U index as the outer index.

| Source | Index of pole (u, v) |
| --- | --- |
| ASM stream and `BsSurface.Poles` | `v * UCount + u` |
| Fusion `NurbsSurface.getData` | `u * VCount + v` |

Weights use the same order as their poles in each source. A direct comparison of the two lists fails for each surface with more than one row and column.

## Workaround

Keep `BsSurface.Poles` in the ASM order. Reorder the poles and weights before you compare them with Fusion API data. `BoundaryCurve` side 0 takes the first `UCount` poles, and side 3 takes every `UCount`th pole.

## Evidence

Native acceptance compared the Fusion control points with the reordered poles of eight authored surfaces and two edited surfaces. The pole drift was 0 cm, and the knot and weight drift was 0.

- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json)
- [Reorder function `fusion_order`](../../../../../re/Fusion/Reconstruction/ComplexGeometry/NurbsMath.py)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
