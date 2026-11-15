# SOLIDWORKS sketch members keep two width values

The layer visual block and explicit member display state each contain a serialized line width. In the six generation-19000 P01 controls, the inline visual block has no width override. The separate display state stores thin for points and the structural line and normal for perimeter lines. The sketch-wide constraint status reported by the API is also a different field from the member's saved status.

Use the constructor and store path for each record. Preserve both fields when reading. Generate the default visual width and the explicitly requested member width independently. [Field provenance and the P01 controls](../../../../re/solidworks/authoring/SketchStyleFields.md)
