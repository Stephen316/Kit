# Fusion accepts TSM vertices with valence above four

## Expectation

Fusion Form primitives have vertices of valence 3 and 4. A TSM cage with a vertex of valence 5 or more looks unsupported. Kit's `CheckVertices` refused such a cage.

## Actual behavior

Fusion 2706.1.17 imports closed Kit cages with vertices of valence 5, 6 and 8. It converts each cage to a solid body and saves the same topology and grips. `MakeClosedCage` built each cage from a split prism, so every `ValenceOffset` is 0.

| Cage | Grips | Valences | Converted faces, edges, vertices | Saved topology and grips |
| --- | --- | --- | --- | --- |
| Valence5 | 32 | 3 and 4, two of 5 | 15, 35, 22 | Equal |
| Valence6 | 38 | 3 and 4, two of 6 | 18, 42, 26 | Equal |
| Valence7 | 44 | 3 and 4, two of 7 | 21, 49, 30 | Equal |
| Valence8 | 50 | 3 and 4, two of 8 | 24, 56, 34 | Equal |

The converted limit point of an extraordinary vertex uses the Catmull–Clark limit mask. A vertex of valence n has the weight n/(n + 5). Each edge neighbour has the weight 4/(n(n + 5)), and each face diagonal has 1/(n(n + 5)).

| Valence | Centre | Edge neighbour | Face diagonal |
| --- | --- | --- | --- |
| 3 | 3/8 | 1/6 | 1/24 |
| 5 | 1/2 | 2/25 | 1/50 |
| 6 | 6/11 | 2/33 | 1/66 |
| 7 | 7/12 | 1/21 | 1/84 |
| 8 | 8/13 | 1/26 | 1/104 |

## Workaround

`CheckVertices` accepts valence 2 to 8. The limit `KValenceLimit` is 8 because no local cage tests a higher valence.

## Evidence

- [Probe preparation](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Preparation.json)
- [Probe results](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Probe.json)
- [Linearity fit](../../../../../re/Fusion/LocalOracle/FormDocuments/Stencil/Fit.json)
- [Conversion linearity](ConversionIsLinear.md)
