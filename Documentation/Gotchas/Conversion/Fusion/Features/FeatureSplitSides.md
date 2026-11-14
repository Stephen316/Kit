# A split keeps the body on the lower side of its plane

## Expectation

The two pieces of a split body look alike.
Either piece could keep the original body and its number.

## Actual behavior

Fusion keeps the original body for the piece on the lower side of the split plane.
The other piece becomes a new body after every existing body.

| Native control | Plane           | First body (cm³) | Second body (cm³) |
| -------------- | --------------- | ---------------: | ----------------: |
| `SplitXZ`      | XZ, offset 10 mm |              8.0 |              16.0 |
| `SplitXY`      | XY, offset 8 mm  |              9.6 |              14.4 |

In each control the first body lies below the plane in Y or Z.

The new cut faces carry the split operation and a side identifier.
The face on the kept piece has side `1`, and the face on the new piece has side `-1`.
The kept body label gains the split operation with copy index 2, and the new body label gains it with copy index 3.
The progenitor table lists the plane as 1, the kept body as 2 and the new body as 3, with `tagId` 4.

## Workaround

`SplitSolid` returns the lower piece first, with the original body number.
The upper piece takes the next free number.
`AddSplitMut` writes the side identifiers, body labels and progenitors in the native order.
All three split cases passed native acceptance body by body, including the plane edit.

The [XZ split control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/SplitXZ.f3d) and the [XY split control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/SplitXY.f3d) record the evidence.
