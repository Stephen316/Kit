# Grip weights scale the stored grip coordinates

## Expectation

A rational spline keeps its shape when every weight gets the same factor. A T-spline cage with weight 2 on every grip should convert to the unit-weight body.

## Actual behavior

Fusion 2706.1.17 converted the box primitive cage with weight 2 on all 26 grips into a smaller solid. The probe kept every TSM grip coordinate and changed only the weights.

| Cage | Grip weights | Form health | Solid | Area (cm²) |
| --- | --- | --- | --- | --- |
| Box primitive | All 1 | 0 | Yes | 23.560443509000663 |
| Box primitive | All 2 | 0 | Yes | 5.890110877250168 |
| Box primitive | Grip 0 at 2, others 1 | 0 | Yes | 24.28421510514164 |

The uniform area is a quarter of the unit area within 2e-15 cm². Fusion therefore divides the stored coordinates by the weight, so each TSM coordinate is a weighted, homogeneous value. Every cage dimension halves.

The converted cache of a weighted cage stores rational surfaces and curves. Kit's third-pass reader refused all seven weighted archives with `Unsupported Fusion journal qualified field`. The fourth pass reads them.

## Workaround

Treat each TSM coordinate as x · w. `ReadNubsSurf` and `MakeNubsSurf` read and write the rational `nurbs` cache with its form name and weighted poles. `StencilKey` no longer holds the weights, so a weighted cage uses the table of its layout. `ConvertCage` evaluates each stencil row on the homogeneous grips. The [weighted face gotcha](WeightedFaceRationality.md) gives the rule and the native comparison. `ConvertGrid` still refuses weights, because no local archive holds a weighted grid conversion.

## Evidence

- [Probe preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Preparation.json)
- [Probe results](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Probe.json)
- [Weight probe](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/WeightProbe.json)
- [Weight check](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/WeightCheck.json)
