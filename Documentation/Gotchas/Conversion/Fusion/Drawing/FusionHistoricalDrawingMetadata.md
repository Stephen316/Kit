# Historical drawing metadata differs from current F3D profiles

The installed drawing example uses metadata version two, manifest version ten and a legacy u32 where current F3D metadata stores its software version. Current qualified F3D metadata uses a different layout at that position and additional trailing fields. The historical drawing has a single `Documentation[Active]/Design1` segment, but its three companion F3D models also lack ACT/Browser segments. That difference must not be generalized solely by file extension.

The [drawing model](../../../../../re/Fusion/Reconstruction/DrawingModel/DrawingModel.md) records exact offsets. The example's BRep serializer class identifier also has a nonstandard UUID spelling. Matching identifiers and selecting serializers by exact stored version are necessary before using the shared entity framework.

The F2D wrapper references an embedded `AC1027` DWG. A decoded ZIP, metadata stream or drawing-settings record does not reconstruct its sheets and annotations. Keep historical wrapper support, DWG semantic support and native drawing acceptance as separate requirements. Do not project a drawing-root package onto its derived F3D and claim lossless drawing conversion.
