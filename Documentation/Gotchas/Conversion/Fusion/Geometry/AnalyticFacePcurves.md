# Fusion reports coedge curves that the stream does not store

## Expectation

`BRepCoEdge.geometry` returns the stored `pcurve` of the coedge. A coedge without a stored `pcurve` has no parameter curve.

## Actual behavior

In the corpus, no coedge on a plane, cone or torus face stores a `pcurve`. Every coedge on a spline face stores one.

| Face carrier | Coedges | Coedges with a stored `pcurve` |
| --- | --- | --- |
| `plane-surface` | 16781 | 0 |
| `cone-surface` | 712 | 0 |
| `torus-surface` | 4 | 0 |
| `spline-surface` | 716 | 716 |

Fusion 2706.1.17 still returns a `NurbsCurve2D` for each coedge on the plane and cylinder faces of two authored solids. The bodies store pcurves on their spline faces only.

| Body | Stored pcurves | Coedges with a `NurbsCurve2D` |
| --- | --- | --- |
| `CappedTube` | 4, on the spline face | 6, 1 more on each plane cap |
| `DomedCylinder` | 3, on the dome face | 6, 2 more on the cylinder and 1 on the plane |

On the cylinder, each reported curve has 2 poles. Its first parameter is constant at 0 or 1.5, the heights of the circle edges in centimeters. Its second parameter spans 2π. On each plane, the reported curve is closed and has 9 poles on the square around the unit circle.

## Workaround

Do not take a `BRepCoEdge.geometry` value as evidence of a stored `pcurve`. Write a `pcurve` only for a coedge on a spline face. `CreateNurbsBody` raises `ValueError` with `Fusion analytic face uses take no pcurve` for a `NurbsUse.Pcurve` on a plane or cylinder.

## Evidence

- [Topology survey](../../../../../re/Fusion/Reconstruction/ComplexGeometry/SurveyTopology.json), field `pcurves`
- [Authored body run](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Remaining.json), field `coedges` of each check
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
