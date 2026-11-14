# A loft pairs section curves without neighbours

## Expectation

A loft could reuse the extrusion records.
Each side face would name one sketch curve and its two neighbouring curves.
Each edge on the bottom would link back to its sketch curve, as it does for an extrusion.

## Actual behavior

The native `LoftRects` control lofts a 40 × 30 mm rectangle up to a 20 × 10 mm rectangle 30 mm higher.
It differs from an extrusion in four ways.

| Record                        | Native loft                                                                 |
| ----------------------------- | --------------------------------------------------------------------------- |
| `LoftProgenitor`              | Two `SketchCurveProgenitor` sections, one curve from each sketch             |
| `SketchCurveRecipe`           | Empty start and end neighbour lists                                         |
| `BodyProgenitor`              | Face labels `1` to `6`, so both caps are listed with the four sides          |
| Journal                       | Face tags only, with no sketch curve links and no edge tags                 |

The top sketch lies on the loft plane.
Its plane reference names the construction plane instead of the XY origin plane.
Its coordinate system, plane matrix and cached plane all carry the 3 cm lift.
The loft takes four operations: the base sketch, the plane, the top sketch and the loft.

## Workaround

`AddLoftFeat` writes one `LoftProgenitor` for each pair of curves, with tags from 3, and the body progenitor after them.
Both caps and every side carry the loft operation.
`LoftSolid` builds the body as one slab whose roof is the top profile.
It pairs curves by their order in the two profiles, so each side face is exact.
Lines must be parallel and point the same way, and circles must share a centre.
All three loft cases passed native acceptance, including the plane height edit.

The [rectangle loft control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/LoftRects.f3d) and the [circle loft control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/LoftCircles.f3d) record the evidence.
