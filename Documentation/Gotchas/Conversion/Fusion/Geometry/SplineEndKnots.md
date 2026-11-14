# ASM stores clamped end knots once less than the Fusion API

## Expectation

A clamped B-spline of degree p has p+1 copies of each end knot. The ASM knot table and the Fusion API knot vector look equal.

## Actual behavior

The ASM knot table stores distinct knot values with their multiplicities. A clamped end has multiplicity p, not p+1. The pole count is `sum(Multiplicity) - Degree + 1`. `NurbsSurface.getData` and `NurbsCurve3D.getData` return the full vector with p+1 end copies.

| Bicubic `AuthoredPatch` U direction | Value |
| --- | --- |
| ASM `UKnots` | (0.0, 0.4, 1.0) |
| ASM `UMultiplicity` | (3, 1, 3) |
| Poles in U | 5 |
| Fusion knot vector | (0, 0, 0, 0, 0.4, 1, 1, 1, 1) |

A knot table copied from the Fusion vector has one extra knot at each end. Its pole count is then two more than the stream contains.

## Workaround

Write each clamped end with multiplicity equal to the degree. Add one copy of each end knot before evaluation or before comparison with Fusion data. `FullKnots` in `Complex.Authoring.SplineEval` does this.

## Evidence

All 113 byte-exact corpus members read every B-spline block with this pole count. Native acceptance compared the expanded knots with the Fusion knots of every authored surface and edited surface. The knot drift was 0.

- [Native acceptance](../../../../../re/Fusion/LocalOracle/ComplexGeometry/NativeAcceptance.json)
- [Preparation with the expected knot vectors](../../../../../re/Fusion/LocalOracle/ComplexGeometry/Preparation.json)
- [Complex verification](../../../../../re/Fusion/Reconstruction/ComplexGeometry/VerifyComplex.json)
- [Complex geometry change entry](../../../../Changes/Fusion/Geometry/FusionComplexGeometry.md)
