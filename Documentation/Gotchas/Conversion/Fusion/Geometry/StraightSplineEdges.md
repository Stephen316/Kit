# Fusion reports a straight B-spline edge as a line

## Expectation

An edge that the ASM stream stores as an `exact_int_cur` B-spline reads back from the Fusion API as `NurbsCurve3D`.

## Actual behavior

Fusion 2706.1.17 reports a straight B-spline edge as `Line3D`. The stored record stays an `intcurve-curve` with an `exact_int_cur` definition. A curved B-spline edge reads back as `NurbsCurve3D`.

| Body | Stored edge curves | Fusion edge types |
| --- | --- | --- |
| `AuthoredPatch` | 4 curved cubic `exact_int_cur` | 4 `NurbsCurve3D` |
| `AuthoredRational` | 4 curved rational `exact_int_cur` | 4 `NurbsCurve3D` |
| `AuthoredPillow` | 12 cubic `exact_int_cur` with collinear, evenly spaced poles | 12 `Line3D` |

A `Line3D` has no control points. A pole comparison through the API is not possible for that edge.

## Workaround

Classify an edge from the stored subtype, not from the API curve type. For a straight edge, compare its end points and sample points with the line. Native acceptance compared pole drift only for `NurbsCurve3D` edges.

## Evidence

- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json)
- [Pillow edge builder `PillowEdges`](../../../../../tests/convert/formats/FusionCodec/Brep/Complex/NurbsSamples.py)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
