# Crease edge class and splits follow the crease angle

## Expectation

Fusion converts a cage with a fixed linear map. Each crease edge of one layout should therefore keep one edge structure and one stored class.

## Actual behavior

The surfaces, curves and points follow the linear map. The crease edges do not. Fusion 2706.1.17 labels a converted edge piece from the signed dihedral angle between the two faces along it.

- A piece is `tangent` when its largest absolute angle, edge ends included, is at most 1°. Otherwise it is `unknown`.
- Sign, scale and edge length do not matter. Folds of 0.99999° and 1.0° stay `tangent`. Folds of 1.000001° and up become `unknown`.
- There is no band of doubt. The old Kit band from 0.65° to 1.15° was a gap in the data, not in Fusion.
- Fusion splits a piece at a knot where the faces meet flat over a whole knot span. Fusion also splits a piece at a knot where the angle touches zero without changing sign.
- A sign change exactly at a knot with both sides past 1° splits into two `unknown` pieces. A sign change away from a knot with one side within 1° stays one `unknown` edge.
- Editing a Form (`startEdit`, move a vertex, `finishEdit`) gives the same result as importing the edited cage.

- A zero of the angle can lie away from a knot. Fusion splits at that exact zero when both sides pass 1° within the knot span of the zero and its neighbour span. The new vertex lies on the curve at that zero. All pieces keep the curve, the label and the label windows.
- On the held-out crease loop torus, Fusion split the meridian at 1.4693578134647791 and 4.491317241470378. Bisection on the angle gives 1.4693578134647796 and 4.491317241470378.

A sign change inside a cage span, with both sides past 1°, gets exactly one cut. The cut is at the zero or at a cage knot. Crease rounds 12 to 21 (3832 curve groups) recovered where it goes:
- The run on each side is the furthest cage knot whose stretch to the zero stays within 1°. A side is confined when its run reaches the end span of the edge.
- The lean compares how fast the turn grows at the two 1° crossings next to the zero. Within a relative difference of 3.05e-4, the square of the 1° limit in radians, the sides tie. Measured ties reach 4.9e-5, and the smallest real lean is 6.3e-4.
- A side is steep when the turn grows faster than 0.01 rad per unit length, measured both per parameter and per cm of chord.
- A steep start or end span cuts at the knot after the left run. Otherwise an unconfined tie cuts at the zero. A confined side that leans steeper cuts at its inner run knot. The other combinations cut at the zero or at the edge's first or last inner knot.
- The refinement knots at 1/8, 1/4 and 1/2 of the end span are never cut points.

## Workaround

`ClassifyEdges` measures the signed angle at eight points per knot span, with both ends included, and refines the peak with a golden-section search.
- It splits at flat knots.
- It splits at sign changes that pass the two-sided 1° test. It finds each zero by bisection to the last bit and adds a vertex there.
- It labels each piece by the 1° rule.
- It cuts a sign change inside a span by the one-cut rule above.
- It raises `ValueError` for more than one sign change on an edge and for a tangent run it cannot bound. It raises the same error for a disagreement between the two steepness measures and for three undecided branches. It also raises for a cut inside a span that holds only the refinement knots of both its ends.

The rule was fitted on rounds 12 to 15, 17, 18 and 21. Held-out rounds 16, 19 and 20 matched 12 of 17, 16 of 18 and 15 of 16 groups before the refit. The miss in round 20 now raises. Over rounds 12 to 21, 155 groups that raised before now match, 25 raise, and none differ.

Near a dart, one crease span can hold the refinement knots of both its ends. In 9 such crease-end cages, Fusion cut at one of those knots 6 times and at the zero 3 times. The rule cannot tell them apart yet, so `ClassifyEdges` raises for a cut inside such a span.

The rule was replayed over 1484 Fusion-saved Form archives, 44 of them unreadable. Of 41863 shared curve groups, 41811 match Fusion's pieces and labels, and 38 are refused. Another 14 groups differ: 13 are in crease-end probe saves and one is the wide L-turn probe. The replay also converted every cage that the general rules accept. 793 bodies matched Fusion's pieces and labels, 10 were refused, and none differed.

The creased box crease ends at a dart. Fusion splits that edge at the dart knot into a `tangent` piece and an `unknown` piece, which the flat-span rule predicts.

## Evidence

- [Crease rule and its constants](../../../../../re/Fusion/Reconstruction/FormDocuments/Crease/CreaseRule.json)
- [Rule replay over saved archives](../../../../../re/Fusion/Reconstruction/FormDocuments/Crease/CreaseRuleCheck.json)
- [One-cut rule and its decision table](../../../../../re/Fusion/Reconstruction/FormDocuments/Crease/CreaseSplitNotes.md)
- [Lean measures per case](../../../../../re/Fusion/Reconstruction/FormDocuments/Crease/CreaseTilt.json)
- [Per-cage crease pieces](../../../../../re/Fusion/Reconstruction/FormDocuments/Crease/CreaseSummary.json)
- [Probe cages and results](../../../../../re/Fusion/LocalOracle/FormDocuments/Crease/)
