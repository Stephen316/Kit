# The two pcurves of a seam lie one period apart

## Expectation

A seam edge of a closed spline face has one parameter curve. The reversed use runs on the same curve in the other direction.

## Actual behavior

Each use of a seam edge has its own `pcurve` record. The two curves lie on opposite ends of the closed direction. One use has an `OffsetU` or `OffsetV`, and the other use has none. The corpus puts the offset on either use. The [closed face survey](../../../../../re/Fusion/Reconstruction/ComplexGeometry/SurveyClosedFaces.json) found 31 seams in the 507 byte-exact `.smb` members.

| Surface | Offset | Use with the offset | Seams |
| --- | --- | --- | --- |
| `loft_spl_sur` | `OffsetU` 1 | Forward | 16 |
| `loft_spl_sur` | `OffsetU` 1 | Reversed | 4 |
| `loft_spl_sur` | `OffsetV` 1 | Reversed | 2 |
| `cl_loft_spl_sur` | `OffsetU` 1 | Forward | 5 |
| `sweep_sur` | `OffsetU` -2π | Reversed | 4 |

Fusion 2706.1.17 reports the coedge curve of each use with its offset added. Three authored solids showed this through import, save and reopen. Each offset is one period of its closed direction.

| Body | Closed directions | Seam edges | Use with the offset | Coedge curves equal to the prediction |
| --- | --- | --- | --- | --- |
| `CappedTube` | U | 1 | Forward, `OffsetU` 1 | 4 of 4 |
| `DomedCylinder` | U | 1 | Forward, `OffsetU` 1 | 3 of 3 |
| `NurbsTorus` | U and V | 2 | Forward `OffsetU` 1 on one seam, reversed `OffsetV` 1 on the other | 4 of 4 |

## Workaround

Give one use of each seam an offset of plus or minus one period in exactly one closed direction. `CreateNurbsBody` raises `ValueError` with `Fusion seam uses must lie one period apart` otherwise. The readers keep corpus offsets as stored and do not check them.

## Evidence

- [Closed face survey](../../../../../re/Fusion/Reconstruction/ComplexGeometry/SurveyClosedFaces.json), field `seamOffsets`
- [Authored body run](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Remaining.json)
- [Second-pass preparation](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Preparation.json), field `coedges` of each authored body
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
