# SOLIDWORKS blind boss direction

The SOLIDWORKS reader now maps the native one-sided blind boss reverse flag to the typed extrusion's reverse field and the direction multiplier used by downstream projections.

A04c's discovery census at `af8257e5` decoded the P03 baseline, YZ and reversed variants. The native end spec distinguished the reversed boss with code 1 while the neutral result still reported forward extrusion. The saved parts measured an unchanged 8,000 mm³ volume and a centroid shift from +5 mm to −5 mm along world Z. The [end-spec trace](../../../re/solidworks/records/Serialize.md) identifies the same native direction field.

The discovery census compares both typed direction and the multiplier with the independently measured boss reversal. Cuts, surfaces and other end conditions retain their existing direction mapping. This change covers the operation's reverse flag. Support-frame mapping requires independent evidence. [Baseline census run](https://github.com/TryUniCAD/Kit/actions/runs/43641328892/job/132589421053)
