# Edge rounds on horizontal and curved edges

`FilletSpec` and `ChamferSpec` take `LevelMm`. With a level, each `(x, y)` point in `CornerMm` and `MoreCornersMm` names the horizontal body edge that passes through `(x, y, LevelMm)`. The edge can be a line or an arc. For example, the edge can be a top or bottom edge of a block, or the rim of a disc or a bore. The edge can also be the base of a joined boss or a rim made of lines and corner rounds. Without a level, the points still name vertical corners as before.

```python
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ChamferSpec import (
    ChamferSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ExtrudeSpec import (
    ExtrudeSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.FilletSpec import (
    FilletSpec,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)

Corners = ((0.0, 0.0), (40.0, 0.0), (40.0, 30.0), (0.0, 30.0))
Block = ExtrudeSpec(
    tuple(LineCurve(Corners[Index], Corners[(Index + 1) % 4]) for Index in range(4)),
    20.0,
)
Specification = DocumentSpec(
    Title="Rounded block",
    ParamName="height",
    LengthMm=20.0,
    ProfileKind="part",
    BodyName="Body1",
    Features=(
        Block,
        FilletSpec((40.0, 30.0), 5.0, "Corner rounds", ((0.0, 0.0),)),
        FilletSpec((20.0, 0.0), 2.0, "Top rim", LevelMm=20.0),
        ChamferSpec((20.0, 0.0), 3.0, "Bottom rim", 2.0, LevelMm=0.0),
    ),
)
Payload = EmitDocument(Specification)
```

The fillet keeps the `Radius` parameter, and the chamfer keeps `Distance`, `Distance 2` or `Rotate Angle`. The adapter steps are unchanged.

## Selection

Fusion selects a tangent chain from each picked edge. Kit follows the loop of the cap face from the picked edge, first forward and then backward. Kit continues along the loop while the side faces meet with the same normal. A chain that returns to its start is a closed loop. Examples include the rim of a disc, a slot or a block with rounded corners.

Picked edges that meet at a sharp convex corner of the same loop join into one chain. Picking all four top edges of a block therefore rounds the whole top loop, as a loop selection does in Fusion. The two blends meet on a mitre in the plane that halves the corner. A fillet mitre is a quarter ellipse, and a chamfer mitre is a line.

The Design records hold one `BrepRef` for every edge of every chain, with one progenitor seed per edge. The picked edge comes first, then the edges ahead of it and then the edges behind it.

| Edge                           | Recipe tags                                    | Recipe faces and vertices                       |
| ------------------------------ | ---------------------------------------------- | ----------------------------------------------- |
| Line or arc in a chain         | Side face, cap, previous and next neighbour   | Side face and cap, one vertex at each end       |
| Full circle with its own tag   | Rim edge, side face, cap                      | Side face and cap, one seam vertex              |
| Full circle without a tag      | Side face, cap                                | Side face and cap, no vertex                    |

The base of a joined boss is a circle without its own tag, because the boolean makes it. The cache of each edge runs in Fusion's edge direction, described in [the chamfer legs gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureChamferLegs.md).

## Geometry

The solver keeps the prism model and applies edge rounds last, to the finished body. Each chain removes a swept section along its edges.

| Edge      | Fillet face                | Chamfer face                       |
| --------- | -------------------------- | ---------------------------------- |
| Line      | Cylinder along the line    | Plane                              |
| Arc       | Torus about the vertical axis of the arc | Cone through the two leg circles |
| Mitre     | Quarter ellipse edge between two cylinders | Line between two planes |

Each blend face takes the feature operation and its own number in chain order. Faces next to the chain are trimmed to the new spring edges. A chain end must meet a flat end face square to the edge. The mass and the area are exact. The swept section is integrated along each line and each arc, and along a mitre the section length changes linearly.

A chamfer's first distance, or its distance with an angle, lies on the face whose loop runs with the picked edge in Fusion's edge direction. On an upward cap that is the cap, except on an arc made by a vertical-edge fillet. On a downward cap it is the side face. The whole chain takes the side of its picked edge. [The chamfer legs gotcha](../../../Gotchas/Conversion/Fusion/Features/FeatureChamferLegs.md) gives the evidence.

## Native acceptance

`AcceptRounds.py` runs the acceptance script on 30 cases and writes `NativeAcceptanceRounds.json`. The report has status `accepted` in Fusion 2706.1.17, with no document open before or after the run. Each case matched its native control at open, at every rollback marker, after `computeAll` and after the edit. Each case also matched its native control after reopening the export and after its last `computeAll`. The block is 40 × 30 × 20 mm, and the disc has a 10 mm radius. The slot bar is 36 × 16 mm, and the L-shaped bar is the block without a 20 × 15 mm corner. The boss and the bore have a 5 mm radius, and the square post is 20 × 10 mm in the middle of the block. The boss and the post rise 10 mm above the block. Volumes are those of the opened Kit document after `computeAll`.

| Case | Features | Volume (cm³) | Faces, edges, vertices | Edit | Edited volume (cm³) |
| --- | --- | ---: | --- | --- | ---: |
| `RoundTopEdge` | block, 3 mm fillet on the front top edge | 23.92274334 | 7, 15, 10 | `Radius` 4 mm | 23.86265482 |
| `BevelTopEdge` | block, 3 mm chamfer on the front top edge | 23.82000000 | 7, 15, 10 | `Distance` 2 mm | 23.92000000 |
| `BevelTopTwo` | block, 3 mm and 2 mm chamfer on the front top edge | 23.88000000 | 7, 15, 10 | `Distance 2` 1 mm | 23.94000000 |
| `BevelTopAngle` | block, 3 mm at 30° chamfer on the front top edge | 23.89607695 | 7, 15, 10 | `Rotate Angle` 40° | 23.84896207 |
| `RoundTwoEdges` | block, 3 mm fillet on the front and back top edges | 23.84548668 | 8, 18, 12 | `Radius` 4 mm | 23.72530965 |
| `RoundBottomEdge` | block, 2 mm fillet on the right bottom edge | 23.97424778 | 7, 15, 10 | `Radius` 3 mm, height 25 mm | 29.94205750 |
| `RoundDiscRim` | disc, 3 mm fillet on the top rim | 6.16996284 | 4, 3, 3 | `Radius` 2 mm | 6.23165947 |
| `BevelDiscRim` | disc, 2 mm chamfer on the top rim | 6.16589918 | 4, 3, 3 | `Distance` 3 mm | 6.02871630 |
| `RoundBossBase` | block, boss, 2 mm fillet at its base | 24.81477531 | 9, 15, 11 | `Radius` 3 mm | 24.85420741 |
| `RoundHoleRim` | block, through bore, 2 mm fillet on its rim | 22.39982653 | 8, 15, 11 | `Radius` 1 mm | 22.42216057 |
| `RoundRimChain` | block, 5 mm corner rounds, 2 mm fillet on the top rim | 23.46039741 | 18, 40, 24 | `Radius` 3 mm | 23.32510944 |
| `BevelRimChain` | block, corner rounds, 2 mm chamfer on the top rim | 23.31634205 | 18, 40, 24 | `Distance` 1 mm | 23.50613556 |
| `RoundSlotRim` | slot bar, 2 mm fillet on the top rim | 10.34616353 | 10, 20, 12 | `Radius` 3 mm | 10.25503036 |
| `BevelBottomTwo` | block, 3 mm and 2 mm chamfer on the right bottom edge | 23.91000000 | 7, 15, 10 | `Distance 2` 1 mm | 23.95500000 |
| `BevelSideAngle` | block, 3 mm at 30° chamfer on the right top edge | 23.92205771 | 7, 15, 10 | `Rotate Angle` 40° | 23.88672155 |
| `BevelDiscTwo` | disc, 3 mm and 2 mm chamfer on the top rim | 6.11353930 | 4, 3, 3 | `Distance 2` 1 mm | 6.19836231 |
| `BevelBoreAngle` | block, bore, 2 mm at 30° chamfer on its rim | 22.38809089 | 8, 15, 11 | `Rotate Angle` 40° | 22.36945186 |
| `BevelTopLoop` | block, 2 mm chamfer on all four top edges | 23.73066667 | 10, 20, 12 | `Distance` 3 mm | 23.40600000 |
| `RoundTopLoop` | block, 2 mm fillet on all four top edges | 23.88289082 | 10, 20, 12 | `Radius` 3 mm | 23.73995568 |
| `RoundTopPair` | block, 3 mm fillet on the front and right top edges | 23.86738934 | 8, 17, 11 | `Radius` 2 mm | 23.94067845 |
| `RoundBottomLoop` | block, 2 mm fillet on all four bottom edges | 23.88289082 | 10, 20, 12 | `Radius` 3 mm | 23.73995568 |
| `BevelBossTwo` | block, boss, 2 mm and 1 mm chamfer at its base | 24.82100288 | 9, 15, 11 | `Distance 2` 1.5 mm | 24.83880524 |
| `BevelDiscBottom` | disc, 3 mm at 30° chamfer on the bottom rim | 6.12936814 | 4, 3, 3 | `Rotate Angle` 40° | 6.06584310 |
| `BevelRimTwo` | block, corner rounds, 2 mm and 1 mm chamfer on the top rim, picked on a line | 23.44356919 | 18, 40, 24 | `Distance 2` 1.5 mm | 23.37995562 |
| `BevelArcTwo` | the same, picked on a corner arc | 23.44147480 | 18, 40, 24 | `Distance 2` 1.5 mm | 23.37838483 |
| `BevelArcBottom` | the same on the bottom rim | 23.44147480 | 18, 40, 24 | `Distance 2` 1.5 mm | 23.37838483 |
| `RoundStepEdge` | L-shaped bar, 2 mm fillet on the inner step edge | 17.98283185 | 9, 21, 14 | `Radius` 3 mm | 17.96137167 |
| `BevelStepTwo` | L-shaped bar, 2 mm and 1 mm chamfer on the inner step edge | 17.98000000 | 9, 21, 14 | `Distance 2` 1.5 mm | 17.97000000 |
| `RoundPostEdge` | block, square post, 2 mm fillet on its front base edge | 26.01716815 | 12, 27, 18 | `Radius` 3 mm | 26.03862833 |
| `BevelPostTwo` | block, square post, 2 mm and 1 mm chamfer on its front base edge | 26.02000000 | 12, 27, 18 | `Distance 2` 1.5 mm | 26.03000000 |

The first 13 cases fixed the geometry. `BevelTopTwo`, `BevelTopAngle`, `BevelBottomTwo`, `BevelBossTwo` and `BevelArcTwo` fixed the chamfer leg rule. `BevelArcBottom`, `BevelStepTwo` and `BevelPostTwo` were added after the rule and matched on their first run. `RoundStepEdge` ends at a concave corner, where the fillet runs into the wall of the step. `RoundPostEdge` is concave and ends flush with the sides of the post.

## Verification

`RoundTests.py` checks the solids against four native controls, the records and the journal tori. It also checks the leg side on top, bottom and corner-round edges, the loop volumes against closed forms and the rejects. `SuiteEvidenceTests.py` checks the report and its digests. Tests run remotely, and no local tests were executed.

## Limits

| Request                                                                       | Status                     |
| ----------------------------------------------------------------------------- | -------------------------- |
| Edges between a cap and a leaning, drafted or swept side face                 | Rejected with `ValueError` |
| Other solid features after an edge round                                      | Rejected with `ValueError` |
| Chain ends that meet a curved face or a face that is not square to the edge   | Rejected with `ValueError` |
| Picked edges that meet at a concave corner or on a concave edge loop          | Rejected with `ValueError` |
| Two picks on the same chain                                                   | Rejected with `ValueError` |
| A fillet radius that reaches the axis of a circular edge                      | Rejected with `ValueError` |
| Vertical and horizontal edges in one feature, and corners where three blends meet | Not authored           |
| Variable radius, setback corners and chord-length fillets                     | Not authored               |
| Edge rounds on revolve bodies                                                 | Not tested in Fusion       |
