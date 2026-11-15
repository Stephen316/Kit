# Source archives can survive outside payload records

The SOLIDWORKS reader's source-retention path stores original archive bytes under document metadata key `solidworks_source_bytes`.
Neutral JSON can preserve those bytes even when the feature timeline and B-rep are typed.
Checking only `BrepPayload` records therefore does not establish that retained native bytes are absent.
The same bytes can also survive in a typed feature's attributes, sketch or
assembly attributes, a source record, or a nested provenance record. A scan
limited to `CadDocument.metadata` misses these legal serialization paths.

The CLI refuses that retained-source key regardless of its value, and refuses binary metadata values under aliases or nested containers.
The scan follows every dataclass field, mapping and supported collection in the
whole document graph, including embedded documents, source and provenance
records. Moving retained bytes into another record does not qualify them.
Use `kit decode` for inspection; replacing the source archive with a digest or text provenance does not create new conversion qualification.

JSON process fixtures cover `bytes` and its supported map/list/tuple/set/frozen-set containers.
Record-placement cases retain the actual SOLIDWORKS archive in feature, sketch,
assembly, source and provenance attributes at both root and nested levels.
Digest and text attributes at those same locations remain positive process cases.
The wire serializer does not support `bytearray`, `memoryview`, or cyclic containers, so those broader scan branches cannot be reached through an ordinary JSON source fixture.
See [the change entry](../../../Changes/Commands/RetainedMetadataGuard.md).
