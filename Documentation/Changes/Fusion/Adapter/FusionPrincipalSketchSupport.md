# Saved Fusion principal sketch supports

The public Fusion reader now records a saved XY or YZ datum as the sketch's native support when the explicit partial read resolves the complete selection route. The sketch keeps its own frame, identifier, origin and in-plane axes. Read a source with the normal adapter registry. [Public API](../../../../src/convert/api/ApiOpen.py)

```python
from convert import open_document

document = open_document("Part.f3d", strict=False)
for frame in document.support_planes:
    if frame.attributes.get("fusion.native_support_resolved"):
        print(frame.attributes["fusion.native_support_name"])
```

The sketch feature and its controller must independently name the same selection descriptor. Its entity leaf must name a typed origin datum in the sketch component's reciprocal origin container. The datum's saved name, zero origin and matching sketch-frame normal qualify the attachment. The frame's attributes retain the saved name and `fusion.native_support_object_id`. Its provenance includes the feature, controller, descriptor, entity leaf, datum, origin container and component. [Saved P01 evidence](../../Research/Readers/FusionRectangleSketchEvidence.md), [Saved P03 evidence](../../Research/Readers/FusionBossProfileEvidence.md)

The partial path leaves unsupported attachment forms unresolved and retains the cached frame. This includes the P04 cut's face attachment. Qualification of the saved sketch datum does not extend the strict native-state contract or establish editable conversion. The strict path still uses the existing complete-document checks. [Strict contract](FusionPublicAdapter.md), [Sketch datum and basis](../../../Gotchas/Conversion/Fusion/Api/FusionDatumBasis.md)

The record route is corroborated by six pinned P01 and eight pinned P03 Fusion archives, including both YZ controls. Hosted registry scenarios are provided for both families' XY and YZ files and for the P04 face-selection boundary. Fresh-process readback and editable acceptance remain open. [Repository integration scenarios](../../../../tests/Research/Archives/ArchiveEvidenceTests.py)
