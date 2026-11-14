# Fusion draws a view from its stored edges

Fusion 2706.1.17 does not find a view's visible edges when it opens a drawing.
Each `ACDBVIEWREP` body lists the edges the view shows, with an edge id, a cached curve and the drawn entity.
On open, Fusion projects only those edges, in the view direction the DWG gives.

A view with no stored edges opens with no curves.
The edges come back when the view updates, for example when its scale changes.
The update finds the visible edges from the referenced body and the view direction.
So Kit computes each view's edges from the view source solid and stores them in Fusion's form.

Grafts on the A3 control showed this.
The control has a base view with 5 edges and two projected views with 4 edges each.

| Graft | Change | Curves after open | Curves after a scale change and back |
| ----- | ------ | ----------------- | ------------------------------------ |
| `V7NoEdges` | Every view's edge list emptied, as Kit writes it | 0, 0 and 0 | 5, 4 and 4, at the control's places |
| `V3AboveBelow` | The right view turned into a view below the base | The 4 stored edges, flattened to a line at the box's edge | A 160 × 40 mm outline at the planned place |
| `V8AboveBelowNoEdges` | `V3AboveBelow` with no edges | 0, 0 and 0 | The same outlines as `V3AboveBelow` |
| `V2RightBack` | The above view turned into a back view right of the right view | The 4 stored edges, flattened to a line | 5 curves in a 160 × 80 mm outline at the planned place |

Marking the view actions, their dependencies or their network as changed did not make Fusion find the edges on open.
Neither did view flag 0x2000, which only views made through the API carry.
All four of those grafts opened with empty views.

A view that keeps its stored edges after its direction changes shows the old edges seen from the new side.
Kit must not change a Fusion view's direction without dropping its edges.

The [T10 report](../../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT10.json) holds the curve counts and boxes of rounds T10 to T15.

Round T16 grafted Kit's stored edges onto the control in four layouts and both styles.
Every view showed Kit's curves on open, with the counts and boxes Fusion gave after its own update.
Fusion's recomputed edges, read from an export, equal Kit's in all 24 views.
The [T16 report](../../../../../re/Fusion/Reconstruction/Drawings/Rules/GraftRoundT16.json) holds the results.

Fusion stores a hidden edge only in the hidden style.
A view switched from hidden to visible style keeps its hidden rows, with invisible entities.
A view Fusion computes in visible style has none, and Kit writes that form.

Kit raises for an edge split into pieces, a part arc edge, a tangent edge and surfaces other than planes, cylinders and cones.
No Fusion save shows how it stores them, and a wrong guess would draw a wrong view on open.
