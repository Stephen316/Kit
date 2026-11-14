# The first chamfer distance follows the edge direction

## Expectation

A chamfer on a horizontal edge takes a first distance and a second distance or an angle.
Kit first put the first distance on the cap, the top or bottom face next to the edge.
Kit put the second leg on the side face.
That rule held for the top edges it was fitted on.

## Actual behavior

On the bottom edge of a block, Fusion put the first distance on the side face.
`BevelBottomTwo` asks for 3 mm and 2 mm on the bottom edge at x = 40 mm.
The native control has its centre of mass at x = 1.992723 cm.
A 2 mm leg on the bottom face gives that value, and a 3 mm leg on the bottom face gives 1.992848 cm.
The base of a boss and a chain seeded on a corner round broke the next guesses in the same way.

The edge caches in the Fusion saves give the edge directions.
Each horizontal edge made by an extrude, a cut or a join runs with the loop of its cap when the cap faces up.
It runs with the loop of its side face when the cap faces down.
An edge made by a fillet on a vertical edge runs with the loop of the fillet face, so it runs against an upward cap.

| Edge in the native saves                     | Cap faces | Edge cache direction           | Face with the first distance |
| -------------------------------------------- | --------- | ------------------------------ | ---------------------------- |
| Top edges of a block                         | Up        | With the top face loop         | Top face                     |
| Bottom edge of a block                       | Down      | +Y, with the side face loop    | Side face                    |
| Top and bottom rim of a disc                 | Up, down  | Normal +Z both times           | Top face, side face          |
| Top rim of a bore                            | Up        | Normal −Z, with the top face   | Top face                     |
| Base of a joined boss                        | Up        | Normal −Z, with the top face   | Top face                     |
| Corner round arc on a block rim, top         | Up        | Normal −Z, with the round face | Round face                   |
| Corner round arc on a block rim, bottom      | Down      | Normal +Z, with the round face | Round face                   |

The first distance, or the distance of a distance-and-angle chamfer, lies on the face whose loop runs with the selected edge.
In a tangent chain the selected edge decides for the whole chain.
`BevelRimTwo` is seeded on a straight edge and `BevelArcTwo` on a corner arc of the same rim, and the chamfers differ only in that choice.

## Workaround

`CornerSolid` records the label of each vertical-edge fillet face in `PrismSolid.Blends`.
`IsWithCap` in `RoundGroup.py` applies the direction rule to one edge.
`PlanLegs` swaps the legs of a chain when its selected edge runs against the cap.
`LevelPicks` writes each edge cache in the same direction.
So the start point, the displacement, the arc normal and the reference vector match the native caches.
The rule was formed from the ten chamfer controls of the earlier runs. `BevelArcBottom`, `BevelStepTwo` and `BevelPostTwo` were added after it and matched their controls on the first run.
[Edge rounds](../../../../Changes/Fusion/Features/FusionEdgeRounds.md) lists every case.
