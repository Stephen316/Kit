# A collapsed spline side has no edge

## Expectation

A face on a B-spline surface has a boundary edge on each side of its parameter rectangle. A side that collapses to one point has a degenerate edge, like a cone apex.

## Actual behavior

A singular code of 1 or 2 collapses the low or high side of one direction to one point. The loop of the face has no edge on that side. The adjacent edges end at the apex vertex.

The [closed face survey](../../../../../re/Fusion/Reconstruction/ComplexGeometry/SurveyClosedFaces.json) read the 507 byte-exact `.smb` members of the corpus.

| Item | Corpus count |
| --- | --- |
| Faces with a singular B-spline side | 4 `loft_spl_sur` faces of lofts to a point |
| Uses in the loop of each face | 3 |
| Seam edges in each loop, each used in both senses | 1 |
| Closed edges in each loop | 1 |
| Edges without a curve in these loops | 0 |
| Uses of edges without a curve in all 507 members | 14, all on `cone-surface` faces |

Fusion 2706.1.17 accepted two authored bodies with the same convention. Each kept its topology, area and surface poles through import, save and reopen.

| Body | Singular side | Edges | Vertices | Area relative error |
| --- | --- | --- | --- | --- |
| `CollapsedPatch` | High V of an open sheet | 3 | 3 | 2.7e-14 |
| `DomedCylinder` | High V of the U-closed dome face | 3 | 3 | 8.4e-15 |

## Workaround

Do not write an edge on a singular side. End the adjacent edges at the apex vertex. `CreateNurbsBody` requires all poles of the collapsed side within 1e-6 cm of one point. Keep the degenerate edge without a curve for an analytic apex only, as the [degenerate edge gotcha](DegenerateHoleEdges.md) describes.

## Evidence

- [Closed face survey](../../../../../re/Fusion/Reconstruction/ComplexGeometry/SurveyClosedFaces.json)
- [Authored body run](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Remaining.json)
- [Analysis](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Analysis.json), field `authored`
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
