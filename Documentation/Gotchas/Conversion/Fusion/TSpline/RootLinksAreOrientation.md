# TSM root links change the solved body

## Expectation

The `f <link>`, `e <link>` and `v <link> NORTH` records look like allocation bookkeeping. Two TSM files with the same control points, creases and face incidence seem to describe the same surface. A writer can apparently choose any incident link as the root.

## Actual behavior

The root links are orientation state of the T-spline basis functions. A different root gives the same control cage but different BRep numerics after conversion.

Fusion 2706.1.17 imported controlled 17 × 23 × 31 mm box cages. Each cage had equal control-point, smooth-point, crease and face-incidence hashes to Fusion's own box primitive.

| Cage roots | Default area (cm²) | Very-high-accuracy center | Equal to primitive |
| --- | --- | --- | --- |
| First incident links | 12.710561939032758 | Differs | No |
| Native face origins only | 12.7105676688771 | Differs by about 3e-6 cm | No |
| Native face origins and edge origins | 12.7105676688771 | Differs by about 3e-6 cm | No |
| Native face, edge and vertex roots | 12.710567668877099 | Equal | Yes |

Face origins control the default-accuracy area and volume. Vertex and edge roots then control the very-high-accuracy center of mass. The difference is small, about 4.5e-7 relative in area, but it is deterministic and survives edits, save and reopen.

## Workaround

Treat face origin, vertex orientation and edge origin as typed model fields. Preserve them exactly when re-emitting a decoded TSM. When authoring, set them explicitly with `CageOrientation` in `MakeClosedCage`. The face origin is the first vertex of each face loop. Do not reorder face loops or renumber links without also carrying these roots.

The `ver` record is an edit counter that Fusion increments on export. Setting it to the native value alone does not change the solved body.

## Evidence

- [Root-variant capture](../../../../../re/Fusion/LocalOracle/TSplineCodec/RootVariants/Capture.json)
- [Edge-variant capture](../../../../../re/Fusion/LocalOracle/TSplineCodec/EdgeVariants/Capture.json)
- [T-spline native acceptance](../../../../../re/Fusion/LocalOracle/TSplineCodec/NativeAcceptance.json)
- [T-spline codec change entry](../../../../Changes/Fusion/TSpline/FusionTsplineCodec.md)
