# Saved SOLIDWORKS rectangle support

The public SOLIDWORKS reader uses the saved attachment for ordinary generation-19000 P01 and P03 rectangle profiles. It rebuilds the selected configuration map, reads the principal datums and Origin, then follows the authored sketch, its local reference and its owned contour cache. The sketch and datum must agree on the owner, world origin, complete right-handed basis and unit scale. The supported P01 path reaches the resolved stream end. The P03 profile reaches its typed extrusion boundary.

The neutral sketch records `typed-archive-reference` as its support source and retains the resolved-stream span of the feature ID. A YZ sketch uses the saved Right Plane and its original basis. [Independent rectangular evidence](SolidWorksRectangularPlaneEvidence.md), [profile closure](SolidWorksContourSuffix.md), [saved geometry and relations](SolidWorksPublicSketchGeometry.md)

Hosted API checks cover the saved reference, world frame and raw provenance across all fourteen P01 and P03 captures. The research reports independently compare the geometry and placement with licensed SOLIDWORKS reopens. Editable round-trip acceptance remains open.

The same ordinary list now reads the P03 blind boss through its saved profile pointer, body chooser, end specification, depth display and final list footer. The typed depth scalar sets the neutral feature and its existing parameter in millimetres. The inch-display control retains its 10 mm authored depth. The reversed variant retains the signed direction. Profile, end-specification and scalar spans point to the original resolved stream. [Independent P03 measurements](SolidWorksRectangularPlaneEvidence.md)
