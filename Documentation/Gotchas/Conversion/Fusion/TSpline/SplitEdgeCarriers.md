# Split converted edges share their curve and pcurve

## Expectation

Each converted Form edge has its own `exact_int_cur` record. Each coedge has its own `exp_par_cur` pcurve over the parameter interval of its edge.

## Actual behavior

Fusion can store one converted edge curve as two edge pieces. The creased box archive has one such pair. Both pieces refer to one `intcurve` record. Each piece stores its own interval in the edge start and end parameters.

The two coedges of the pieces on one face refer to one `pcurve` record. The pcurve knot range is the range of the complete edge curve, not the piece interval. A reversed coedge stores the negated pcurve.

The creased box archive has this layout.

| Item | Count |
| --- | --- |
| Faces | 6 |
| Edges | 13 |
| `intcurve` records | 12 |
| Coedges | 26 |
| `pcurve` records | 24 |
| Split pieces | Edge 6 with bounds (−1, 0) and edge 7 with bounds (−2, −1) on one curve with range (−2, 0) |

The other eight local archives have no split edges. Each of their edges has one curve, and each coedge has one pcurve.

## Workaround

Give both pieces the same `FormEdge.Curve` and `FormEdge.Jumps`, and set `FormEdge.Bounds` on each piece. Give each piece use the full-range pcurve in edge sense. `MakeFormLinks` shares one curve record per distinct curve and jump lists. It shares one pcurve record per face, sense, pcurve and fit value.

## Evidence

- [BRep rebuild comparison](../../../../../re/Fusion/Reconstruction/FormDocuments/Sourceless/BrepRebuild.json)
- [Owner order](ConvertedOwnerOrder.md)
- [Discontinuity lists](ConvertedDiscontinuityLists.md)
