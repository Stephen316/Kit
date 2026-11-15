# SOLIDWORKS sketch relation operands

The current and definition operands of a sketch relation can have different point IDs. In eleven licensed generation-19000 P04 parts, the current operand for a document Origin reference belonged to the consuming sketch. The corresponding definition operand belonged to the document Origin sketch. The definition can contain two identical numeric point IDs because those IDs belong to different sketches.

Resolve definition points by their sketch owner and native point ID. Compare the current operand against the proxy in the consuming sketch using its local ID and coordinates. The two P04 cut offsets share the generic distance relation code and ordered point pair. Use the saved distance class and the measured display dimension to distinguish their axes. [Licensed P04 sketch comparison](../../Changes/Research/Readers/SolidWorks/SolidWorksLicensedCutDimensions.md)
