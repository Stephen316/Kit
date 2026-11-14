# Profile circles start at their −X point

## Expectation

A full circle has no corners, so its start point should not matter.
Kit started each profile circle at angle 0, on the +X side of its centre.

## Actual behavior

Native sketch circles start at their −X point.
Fusion then stores each circular edge with a +X major axis and parameters from −π to π.
The seam vertex of the edge sits at −X of the centre.

| Edge in the native `DiscBore` control | Radius (cm) | Major axis | Parameters | Seam vertex      |
| ------------------------------------- | ----------- | ---------- | ---------- | ---------------- |
| Disc rim, top and bottom              | 2.0         | +X         | −π to π    | −X of the centre |
| Source pocket                         | 0.3         | +X         | −π to π    | −X of the centre |
| Pocket copy at 90°                    | 0.3         | +Y         | −π to π    | −Y of the centre |
| Hole bore                             | 0.4         | +X         | −π to π    | −X of the centre |
| Counterbore rim and floor             | 0.7         | +X         | 0 to 2π    | +X of the centre |

Pattern copies turn the seam with the copy.
The counterbore edges come from the hole tool body and keep their own seam.

The native rim recipe of a disc top face names one vertex with UV order (2, 2, 2, 2, 1, 0, 1).
That vertex is the seam vertex, so its position is part of the reference.

## Workaround

`CurveSpan` starts a full profile circle at its −X point.
The wall cylinder and both circular edges then use the native frame.
Hole circles use the same start point, so Kit counterbore edges differ from the native table.
After this change, every re-emitted document except `MultiDiscPart` passed native acceptance.
Its warning had another cause, which the [copy occurrence gotcha](FeatureCopyOccurrence.md) records.

The [native disc control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/DiscBore.f3d) records the seams.
