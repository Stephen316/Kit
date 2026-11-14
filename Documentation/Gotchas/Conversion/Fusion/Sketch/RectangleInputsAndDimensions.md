# Rectangle inputs do not imply sketch dimensions

It is easy to assume that a rectangular source sketch contains horizontal/vertical constraints and driving width/depth dimensions. The ordinary rectangle control used for native Fusion authoring contains neither: `MSketch.constraints`, `MSketch.dimensions`, and `DcSketch.dcParameters` are empty. Its four Line3D entities share four Point3D endpoints, which closes the profile without separate coincidence records.

The independent `rectangle` and `cuboid` writers reproduce that qualified semantic scope. `WidthMm` and `DepthMm` determine the initial corner geometry; they are not native driving sketch parameters. `LengthMm` drives the cuboid extrusion through the explicit user-parameter and `AlongDistance` binding. Do not describe all three dimensions as native editable parameters, or fabricate constraint records from the rectangular appearance alone.

Use a separate, explicitly qualified sketch-dimension constructor when native width/depth parameters are required. The fixed sketch-origin entity is also distinct from the corner at the same coordinates; equal coordinates do not establish a coincidence or anchoring constraint.

Evidence: [complete rectangle research](../../../../../re/Fusion/Reconstruction/RectangleAuthoring/AuthoringPlan.md), especially the decoded Point3D/CurveUses relationships and the empty sketch collections in [ControlGraph.json.xz](../../../../../re/Fusion/Reconstruction/RectangleAuthoring/ControlGraph.json.xz). The public profiles are documented in [FusionRectangleAuthoring](../../../../Changes/Fusion/FusionRectangleAuthoring.md).
