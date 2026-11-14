# The XZ origin plane has a native sketch frame

## Expectation

A sketch on the XZ origin plane only needs a plane through the origin with a Y normal.
Kit wrote its XZ work plane with U along +X and V along +Z.

## Actual behavior

That frame has a −Y normal.
Kit revolve documents opened with the right solid, because the journal stores the solved body.
After `computeAll` or a parameter edit, Fusion swept each partial revolve the other way round the Z axis.

The native XZ work plane stores a different frame.

| Frame         | U axis | V axis | Normal |
| ------------- | ------ | ------ | ------ |
| Kit, rejected | +X     | +Z     | −Y     |
| Native        | +Z     | +X     | +Y     |

## Workaround

`AddGeometryMut` writes the XZ origin plane with the native frame.
After this change, the four revolve cases passed native acceptance, including the recompute and edit checks.

The [native half revolve control](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/RevolveHalf.f3d) records the frame.
