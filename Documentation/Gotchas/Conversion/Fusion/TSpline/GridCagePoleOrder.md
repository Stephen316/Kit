# Grid cage poles do not follow the grip order

## Expectation

A regular grid cage converts to one bicubic B-spline surface whose poles are the grips. The grip order in the TSM member gives the pole grid.

## Actual behavior

Fusion 2706.1.17 converts a qualified open grid cage to one face. Its surface poles are the grips, but in another order. Boundary vertices own compound grips, and the cage link frame decides each grip position.

A qualified cage has these properties.

| Property | Value |
| --- | --- |
| Degree, unit scale and end conditions | 3, 1.0 and `SUBD_CREASES` |
| Interior vertices | Four spokes each |
| Knot intervals | 1.0 on every edge |
| End condition values | 0.0 |
| Grip weights | 1.0 within 2⁻⁵¹ |
| Creases | Boundary edges and boundary vertices only |
| Compound grips | Present, with spoke lengths 0 or 1 |

Kit derives the pole grid with these rules. The converted bodies of 26 archives that Fusion wrote match them within 8.9e-16 cm.

| Item | Rule |
| --- | --- |
| Spoke frame | The vertex origin link is spoke `CageVertex.Direction`: north 0, west 1, south 2, east 3 |
| Fan step | The next link in a fan is `Links[Previous].Opposite`, and the spoke grows by `1 + ValenceOffset` modulo 4 |
| Vertex grid | Face 0 has its origin vertex at (0, 0) and its origin link pointing east |
| Grid steps | North (0, 1), west (−1, 0), south (0, −1), east (1, 0) |
| Vertex pole | Index 0 maps to pole 0, the last index n maps to n + 2, and other indices i map to i + 1 |
| Compound grip | For each linked spoke, one grip one step out, then a corner grip when the next spoke is linked |
| Pole order | Rows of constant V, with U varying fastest |
| Knots | 0 and n with multiplicity 3, every integer between them with multiplicity 1 |
| Patch cell | Face index, local box (0, 1, 0, 1), offset (−row, −column, 0) |
| Boundary curves | First row and last column forward, last row and first column reversed |

A cage outside these properties raises `ValueError`. The census found these refusals in 35 local archives.

| Message | Archives | Cages |
| --- | --- | --- |
| `needs boundary compound grips` | 26 | Closed box and symmetric box cages without a grip mapping |
| `does not convert interior creases` | 7 | Creased plane and creased box cages |
| `needs four spokes per vertex` | 2 | Uncreased box cages with valence-3 corners |

## Workaround

Convert qualified cages with `ConvertGrid`. Do not order the poles by grip index. Write the patch program from the face grid, not from the grip order.

## Evidence

- [Grid census](../../../../../re/Fusion/Reconstruction/FormDocuments/GridCensus.json)
- [Grid acceptance](../../../../../re/Fusion/LocalOracle/FormDocuments/Grid/NativeAcceptance.json)
- [Grid case preparation](../../../../../re/Fusion/Reconstruction/FormDocuments/PrepareGrid.py)
- [Link order and valence](LinkOrderAndValence.md)
- [Form document change entry](../../../../Changes/Fusion/TSpline/FusionFormDocuments.md)
