# The body volume of a NURBS solid is not exact

## Expectation

`BRepBody.volume` gives the volume of a valid solid within the modeling tolerance. It agrees with `getPhysicalProperties` at every accuracy.

## Actual behavior

Fusion 2706.1.17 gave a less exact `BRepBody.volume` for two of three authored solids. Both have a rational, U-closed NURBS face beside plane faces. The torus has one NURBS face only, and its two volumes were equal. `getPhysicalProperties(VeryHighCalculationAccuracy)` agreed with the expected volume. A research evaluator computed each expected volume and checked it with the divergence theorem. `BRepBody.area` was equal to the very high accuracy area for all three solids.

| Body | Expected volume (cm³) | `BRepBody.volume` relative error | Very high accuracy relative error |
| --- | --- | --- | --- |
| `CappedTube` | 6.967693466501751 | 3.26e-5 | 2.30e-11 |
| `DomedCylinder` | 6.850930939543331 | 1.26e-5 | 7.31e-11 |
| `NurbsTorus` | 9.869604401089358 | 2.34e-10 | 2.34e-10 |

The temporary body, the persisted body and the reopened body gave the same values.

## Workaround

Compare a native volume with `getPhysicalProperties` at `VeryHighCalculationAccuracy`. Do not compare `BRepBody.volume` with a relative tolerance tighter than the errors in the table.

## Evidence

- [Authored body run](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Runs/Remaining.json), fields `summary` and `physical`
- [Analysis](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Analysis.json), fields `bodyVolumeRelativeError` and `volumeRelativeError`
- [Second-pass preparation](../../../../../re/Fusion/LocalOracle/ComplexGeometry/SecondPass/Preparation.json), the expected values and their cross-checks
- [Native sheet measurements](FusionSheetMeasurements.md)
