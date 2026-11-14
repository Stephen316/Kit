# Historical mesh parts belong to the editable document

It is tempting to enumerate mesh parts from the current ParaMeshBody geometry reference. That loses valid components owned by earlier mesh features. The combined-face-group control has one visible body but three geometry/trigger/component pairs; the shell control has one visible body but separate source and hollowed geometry components.

The complete document must enumerate every ParaMeshGeometry entity, follow its serializer trigger, verify the reciprocal `rMeshGeometry` reference and resolve the inherited `partName`. Each selected component's `fusion_uuid` must match the geometry's `pMeshUuid`. The UUID in the component filename and the container's own `mesh_uuid` do not provide that join.

Preserve all these components and the existing before/after feature references. Require exhaustive, unique ownership when reading and emitting. Do not omit an older component merely because the final body does not currently display it. The native component acceptance demonstrated rollback to earlier topology and meaningful feature edits after replacing every historical component through the semantic codec.

[The complete inventory](../../../../../re/Fusion/Reconstruction/ParaMesh/MeshJoins.json) covers 103 components and 63 bodies across 52 archives with zero join errors. [The native component report](../../../../../re/Fusion/LocalOracle/ParaMesh/NativeAcceptance.json) records rollback, restoration, combine/shell edits, save and reopen. Complete archive reconstruction has its own acceptance gate in the [document change entry](../../../../Changes/Fusion/Mesh/FusionMeshDocuments.md).
