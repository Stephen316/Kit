# A tolerant vertex is never tighter than its tolerant edges

## Expectation

The tolerances of `tedge-edge` and `tvertex-vertex` records are independent values.

## Actual behavior

The 8 corpus tolerant vertices each meet tolerant edges. Each vertex `Tolerance` equals the largest tolerance of those edges plus 1e-10. `SavedTolerance` equals `Tolerance` on all 8 vertices.

Fusion 2706.1.17 reports the stored values as `BRepEdge.tolerance` and `BRepVertex.tolerance`. Two consistent edits of the `solid_twist.f3d` snapshot showed this after import, persistence, save and reopen.

| Case | Record | Before | After | Reported after |
| --- | --- | --- | --- | --- |
| `TolerantEdge` | Edge tolerance, kept below both end vertex tolerances | 1.6486711089754196e-05 | 2e-05 | 2e-05 on one edge |
| `TolerantVertex` | `Tolerance` and `SavedTolerance` | 2.325530054202186e-05 | 6e-05 | 6e-05 |

## Workaround

Keep each tolerant vertex at least as large as every tolerant edge that ends at it. `ReadGeometry`, `ReadJournal` and both emitters raise `ValueError` with `Fusion tolerant vertex is tighter than its tolerant edge` otherwise.

## Evidence

- [Subtypes run](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Subtypes.json)
- [Preparation](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Preparation.json), cases `TolerantEdge`, `TolerantVertex` and `TolerantOrder`
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
