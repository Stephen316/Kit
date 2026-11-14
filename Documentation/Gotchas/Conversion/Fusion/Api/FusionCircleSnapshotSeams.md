# A full-circle snapshot can use a different seam

A full circle in `CircArc3D.arcCurve` can store start/end angles 0 and 2π while its ASM snapshot edge uses −π and +π. The corresponding seam vertex lies at negative X relative to the circle center. Assuming that every full-circle edge begins at positive X rejects a valid vendor save or changes its kernel parameterization.

The qualified circular projector checks an exact full-turn interval and evaluates the seam vertex from the actual start parameter and carrier normal. The projector also retains every native parameter and endpoint index. The neutral graph represents the same analytic circle. It does not overwrite the native seam with the neutral topology builder's seam.

The circle-only native snapshot has one planar open sheet and a coedge without a partner. An extruded circular snapshot also contains planar sheets beside the closed solid. These are explicit typed topology, not missing solid faces. Sheet and solid incidence are checked separately.

See the [source inventory and model](../../../../../re/Fusion/Reconstruction/PublicRotational/ProjectionModel.md) and [public circular projection](../../../../Changes/Fusion/Adapter/FusionNativeCircularProjection.md).
