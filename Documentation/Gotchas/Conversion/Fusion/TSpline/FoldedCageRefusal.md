# Fusion refuses to convert a folded cage

## Expectation

Fusion converts a T-spline cage with a fixed linear map, so any grip position has a converted body. A writer can store that body for any cage.

## Actual behavior

Fusion 2706.1.17 refused four large single-grip moves of the creased cages. The API raised a conversion error, and the probe recorded no body.

| Cage | Grip | Move (cm) | Fusion result |
| --- | --- | --- | --- |
| Creased plane | 3 | (1, 0, 0) | `ASM_TSP_IG_SURFACE_IRREGULAR` |
| Creased plane | 8 | (1, 0, 0) | `ASM_TSP_IG_SURFACE_IRREGULAR` |
| Creased plane | 10 | (1, 0, 0) | `ASM_TSP_IG_SURFACE_IRREGULAR` |
| Creased plane | 31 | (1, 0, 0) | Converted |
| Creased box | 7 | (2.5, 0, 0) | `ASM_TSP_IG_CURVE_IRREGULAR` |

Each message adds "Edges or faces may be crossing. Review in box mode." The linear map still gives a body for these cages. A Kit document with that body would hold a conversion that Fusion itself refuses.

The Kit bodies of the refused cages fold back on themselves. `FoldCheck.py` sampled four face normals and four edge tangents in each knot span. It took the smallest cosine between neighbouring samples.

| Cages | Count | Smallest face normal cosine | Smallest edge tangent cosine |
| --- | --- | --- | --- |
| Refused by Fusion | 4 | -1.0 in each | -1.0 to 0.947 |
| Converted by Fusion, limit probe | 3 | 0.991 | 0.994 |
| Every Fusion-saved archive that Kit converts | 484 | 0.791 | 0.937 |

A normal cosine of -1.0 means that the face turns over between two samples.

## Workaround

Refuse a body when two neighbouring samples differ by 60° or more. `CheckFolds` applies this rule in `CageBody`, `ConvertForm` and `SwapGridCage`. The 60° limit lies between the refused cages and every converted cage. Fusion may refuse other crossings that the samples miss, such as two distant faces that intersect.

## Evidence

- [Limit probe](../../../../../re/Fusion/Reconstruction/FormDocuments/Stencil/LimitProbe.json)
- [Fold check](../../../../../re/Fusion/Reconstruction/FormDocuments/Cages/FoldCheck.json)
- [Probe results](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Probe.json)
