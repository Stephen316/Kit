# Seam pcurves follow the closure of the edge curve

## Expectation

A converted face that wraps around has a seam edge, and both coedges of that edge lie on the one face. Fusion could place the two pcurves by the closure of the face across the seam. A periodic seam would then share one parameter value, and a seam closed by a crease would have one coedge at each end.

## Actual behavior

Fusion places the two pcurves by the closure of the edge curve. The closure of the seam direction does not decide it.

| Edge curve closure | Forward coedge | Reversed coedge | Pcurve closure |
| --- | --- | --- | --- |
| 2, periodic | Low end of the seam direction | Low end | Same as before |
| 1, closed by a crease | Low end | High end | 1 |
| 0, open | Low end | Low end | 0 |

The progenitor windows of the edge follow the pcurves. A coedge at the low end lists the first row of cage cells with the parameter 0. A coedge at the high end lists the last row with the parameter 1.

These held-out cages show the rule. Each is a torus.

| Cage | Face closure (u, v) | Seam edges |
| --- | --- | --- |
| HeldTorus75, Torus86 | 2, 2 | Both seams periodic, both coedges low |
| HeldCreaseRing, creased parallel | 2, 1 | Crease ring (curve closure 2) low and low. Meridian seam (curve closure 1) low and high |
| HeldCreaseLoop, creased meridian | 1, 2 | Crease pieces (curve closure 2) low and low. Parallel seam (curve closure 1) low and high |
| HeldCreaseCross, both creased | 1, 1 | Both seams low and high |
| HeldCreaseBands, two creased parallels | 2, 0 per face | Meridian seams (curve closure 0) low and low |
| HeldCreaseSlices, two creased meridians | 0, 2 per face | Parallel seams (curve closure 0) low and low |

The rule was read from the first two crease tori. HeldCreaseCross was then built to test it. The rule predicted both of its seams, and a rule keyed on the seam direction predicted neither.

Fusion also numbers the pieces of a split crease in the order of the first use that meets the edge. HeldCreaseSlices meets both crease loops on reversed uses first. So Fusion lists their pieces against the curve direction.

Fusion also stores a seam pcurve with a pcurve offset. The offset is 0 or one full knot span of a closed direction. The full spans are 8 and 6 in Torus86, and 9 in the crease-closed direction of HeldCreaseLoop. Kit writes offset 0. A shift by one full span in a closed direction gives the same curve on the surface. Fusion accepted every Kit document in the general run. The Form tests check that each native offset is 0 or one span, and they compare pcurves up to one span in each closed direction.

Fusion numbers the vertices of the body in the order they first appear in the edge list, start before end. A vertex added by a split takes its place in that order. In HeldWeightedSharp, a box with sharp edges, three crease edges split. Their new vertices sit between the cage corners in Fusion's list, not after them.

## Workaround

`BlockSides` reads which grid axes are seams. An axis is a seam when the last and the first row of cells share cage edges. As a result, a seam closed by a crease counts too. `SideUses` takes the curve closure of the whole side. Then it shifts each seam side by the table above, and `WindowCell` takes the cells across the seam for a shifted side. A closed seam side that the layout splits into several edges raises `ValueError`, because no saved case shows it.

`ClassifyEdges` measures a seam crease from the face side of each coedge. When a coedge's face lies past the end of the domain, it moves that pcurve to the other end for the measure only. `ClassifyEdges` lists the pieces against the curve direction when the first use of the edge is reversed. `OrderPoints` then numbers the vertices by first appearance in the edge list.

## Evidence

- [General acceptance report](../../../../../re/Fusion/LocalOracle/FormDocuments/General/Accept/GeneralAcceptance.json)
- [General notes, session 8](../../../../../re/Fusion/Reconstruction/FormDocuments/General/GeneralNotes.md)
- [Split edge carriers](SplitEdgeCarriers.md)
