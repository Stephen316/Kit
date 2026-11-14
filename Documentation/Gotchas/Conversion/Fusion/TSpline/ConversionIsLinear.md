# Fusion converts a T-spline cage with a fixed linear map

## Expectation

A T-spline cage with extraordinary vertices or creases converts through G1 caps and crease rules. The conversion looks like a geometric fit that only the Fusion kernel can reproduce.

## Actual behavior

Fusion 2706.1.17 converts each cage layout with a fixed linear map. Each converted pole, boundary curve pole and vertex point is a fixed weighted sum of the grips. The layout is the topology with its root links, the grip mapping, the creases, the smart grips, the header rules and the grip weights.

The probe moved one grip at a time by a known step. It also applied axis, scaled, paired and random moves to all grips. Fusion converted every variant in a new Form.

| Cage | Grips | Poles and points | Variants | Largest prediction gap (cm) | Largest row-sum error |
| --- | --- | --- | --- | --- | --- |
| Box primitive | 26 | 1178 | 37 | 4.8e-15 | 3.6e-15 |
| Creased plane | 34 | 88 | 45 | 5.8e-16 | 1.8e-15 |
| Creased box | 26 | 1720 | 37 | 5.8e-15 | 6.2e-15 |
| Kit box with 3 × 3 faces per side | 56 | 1352 | 67 | 2.1e-14 | 1.7e-13 |
| Kit valence-5 prism | 32 | 2362 | 43 | 1.5e-15 | 3.9e-15 |
| Kit valence-6 prism | 38 | 2834 | 49 | 2.7e-15 | 7.1e-15 |
| Kit valence-8 prism | 50 | 3778 | 61 | 5.2e-15 | 3.4e-14 |

A move along x left the y and z coordinates of every pole unchanged. The weights of each pole sum to 1. The fit predicts the symmetric box and a warped valence-5 prism within 1.2e-14 cm, although neither cage took part in the fit.

The map does not depend on the grip positions. Fusion refuses a folded cage instead of applying it, as the [folded cage gotcha](FoldedCageRefusal.md) shows. Every probe used unit weights, and the [weighted grip gotcha](WeightedGripCoordinates.md) explains why. Apart from crease splits, the converted body keeps its face, edge and vertex structure, its knots and its patch cells. Only these fields change with the grips.

| Field | Change |
| --- | --- |
| Surface, curve and vertex points | The linear map |
| Surface jumps and curve discontinuity lists | The jump rule in the [discontinuity gotcha](ConvertedDiscontinuityLists.md) |
| Pcurve poles and fit tolerance | Rounding noise up to 1.8e-15 and 3.2e-14 |
| Crease edge class and crease splits | The crease angle, as the [crease edge class gotcha](CreaseEdgeClass.md) shows |
| Naming identities and time stamps | New values in each document |

## Coefficients

| Part | Coefficients |
| --- | --- |
| Regular B-spline regions | Fractions with small powers of 2 and 3 as denominators |
| Vertex limit points | The Catmull–Clark limit mask of the vertex valence |
| Creased plane | Four distinct values, all fractions |
| G1 caps around extraordinary vertices | Not fractions with denominators up to 1e5 within 1e-14 |

A sample of 40 cap values from each cage was not in Q(√2), Q(√3) or Q(√5) with integer parts up to 5000. Two of the 240 samples hit Q(√3), which chance explains at this density. The valence-5 cap values therefore hold no simple cos(2π/5) term.

The cap values depend on the corner neighbourhood, not on the valence alone.

| Cage pair | Shared cap values |
| --- | --- |
| Box primitive and 3 × 3 box | All 134 of the box primitive |
| Box primitive and creased box | All 134 of the box primitive |
| Valence-5, valence-6 and valence-8 prisms | 347 |
| A box cage and a prism | 0 or 1 |

## Workaround

Convert with a fitted table for each cage layout. `ConvertCage` applies the table. `SwapFormCage` writes the result into a document of the same layout, and `EmitFormDoc` writes a new document. Refuse every layout without a table. A local cap rule could cover new layouts, but no local evidence fixes its neighbourhood.

## Evidence

- [Probe preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Preparation.json)
- [Probe results](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Probe.json)
- [Linearity fit](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Fit.json)
- [Masked body invariance](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/StencilInvariance.json)
- [Coefficient arithmetic](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/StencilFields.json)
- [Shared cap values](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/StencilLocality.json)
- [Valence above four](CageValenceAboveFour.md)
