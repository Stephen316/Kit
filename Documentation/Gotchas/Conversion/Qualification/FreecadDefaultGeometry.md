# FreeCAD default geometry does not prove required features

An encodable sketch or generated `Document.xml` does not establish a complete editable feature.
The earlier generic writer could construct an extrusion with missing length data, create a neutral-only `Part::Feature`, or execute an unproven profile after the source label changed.
Transfer accounting happened after output construction and did not protect direct callers from those paths.

The public adapter now checks required feature expressibility before filesystem work.
It reuses the existing feature checks, closed-profile and topology proofs, and actual editable IDs from the emitter.
Unsupported histories refuse even with carrier output enabled.
The additional in-memory encode has a model-dependent allocation cost and adds no separate hard resource limit.

Use fully specified typed inputs for writer-positive cases.
Keep unsupported inputs available through native reading and explicit model serialization.
See [the qualification change](../../../Changes/Research/Readers/NativeSemanticWriteQualification.md).
