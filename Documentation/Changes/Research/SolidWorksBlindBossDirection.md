# SOLIDWORKS blind boss direction

The SOLIDWORKS reader now maps the native one-sided blind boss reverse flag to the typed extrusion's reverse field and the direction multiplier used by downstream projections.
The body bounding box uses the same flag when projecting the profile through the boss depth. The P03 reversed Front Plane part spans Z = −10 to 0 mm, consistent with its measured centroid at −5 mm.

A04c's discovery census at `af8257e5` decoded the P03 baseline, YZ and reversed variants. The native end spec distinguished the reversed boss with code 1 while the neutral result still reported forward extrusion. The saved parts measured an unchanged 8,000 mm³ volume and a centroid shift from +5 mm to −5 mm along world Z. The [end-spec trace](../../../re/solidworks/records/Serialize.md) identifies the same native direction field.

The discovery census compares typed direction and the direction multiplier against the independent measurements for all eight P03 captures. For the two Front Plane direction cases it derives the expected Z bounds from the measured centroid and depth of the uniform blind boss. The forward and reversed neutral bounds matched at PR head `1bdb6743` on tested checkout `a6d64715`. Support-frame mapping requires independent evidence. [Discovery checks](https://github.com/TryUniCAD/Kit/actions/runs/43652490420/job/132623817084)
