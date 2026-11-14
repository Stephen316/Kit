# Hole placement depends on the cap face root

## Expectation

A hole `DRPoint` stores the hole centre in `point3d`.
Fusion recomputes the hole at that point on the referenced top face.
The `param` field and the face recipe only help to find the face.

## Actual behavior

Native documents store `param` as the offset of the hole centre from the plane root of the top face.
An extruded cap face has its plane root at the centre of the bounding box of the sketch profile.
The `param` signs show a u axis along +X and a v axis along +Y.
A hole at the root uses `refType` 6, and any other hole uses `refType` 17.

| Native control | Profile                      | Hole centre (cm) | `refType` | `param` (cm)  | Spot face recipe   |
| -------------- | ---------------------------- | ---------------- | --------- | ------------- | ------------------ |
| `HoleThrough`  | 4 × 3 rectangle              | (2.0, 1.5)       | 6         | (0, 0)        | `FaceRecipe`       |
| `HoleOffset`   | 4 × 3 rectangle              | (0.8, 0.6)       | 17        | (−1.2, −0.9)  | `BoundFaceRecipe`  |
| `HoleNotch`    | 4 × 3 with a semicircle cut  | (0.8, 0.6)       | 17        | (−1.2, −0.9)  | `BoundFaceRecipe`  |
| `DiscBore`     | Circle of radius 2 at origin | (0, 0)           | 6         | (0, 0)        | `FaceRecipe`       |

The notch profile has its area centroid near y = 1.34 cm, so the root is the box centre, not the centroid.
The plane roots of the native `HoleNotch` and `ProfileSlot` top faces are (2.0, 1.5) and (2.0, 1.0).
Both values are box centres.
The hole axis `DRVector` carries the same `param` as the point.

Kit first wrote `refType` 6 with `param` (0, 0) for every hole.
Off-centre holes opened at the right place.
After `computeAll`, Fusion moved each one to the face centre and ignored `point3d`.
`HoleGrid` and `MultiPocketPart` then failed the native geometry comparison.

The axis face of a hole on a disc is bounded by one closed circular edge.
Kit first wrote that edge with the corner recipe for straight sides, which names the wall twice.
The native `DiscBore` recipe names the rim edge tag and one vertex instead.
`MultiDiscPart` reported `Failed to evaluate the direction due to the invalid input` on its hole with either recipe.
That warning came from the circular pattern before the hole, as the [copy occurrence gotcha](FeatureCopyOccurrence.md) records.

| Recipe part | Native circular top face                                         |
| ----------- | ---------------------------------------------------------------- |
| Tags        | Top face, rim edge (`-1` with the extrusion operation), wall     |
| Edge        | Rim edge tag, faces wall and top                                 |
| Vertex      | Faces wall and top, the rim edge, UV order (2, 2, 2, 2, 1, 0, 1) |

## Workaround

`RoofMiddle` finds the extrusion whose operation created the top face and takes the box centre of its profile.
Arcs count with their axis extremes.
A hole at that centre keeps `refType` 6, `param` (0, 0) and the plain face recipe.
Any other hole uses `refType` 17, the offset from the centre as `param` and the bound face recipe.
`RimRecipe` writes the native single-edge recipe when the top face has one circular boundary.

Only rectangle, notch, slot and disc profiles have native evidence.
Kit assumes the same box rule for other profiles.
The [native hole controls](../../../../../re/Fusion/LocalOracle/FeatureAuthoring/Controls/CaptureFamilies.json) record each case.
