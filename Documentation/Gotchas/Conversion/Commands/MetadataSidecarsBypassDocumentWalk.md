# FreeCAD metadata children are outside the assembly document walk

The CLI's assembly walk checks typed embedded component documents. It does not
discover documents serialized under `metadata.freecad.external_documents`.
FreeCAD's `NativeOuter` reads that metadata separately, and `WriteNative` writes
each child using its own writer options. Qualifying the parent therefore does
not qualify a metadata child or establish native capability transfers for it.

The CLI refuses every nonempty external-document metadata collection before
output publication, including when its owner is nested inside an assembly.
Preserve the source and use `kit decode` or `kit research` for inspection.
Empty external-document collections do not request sidecar publication.

See [the guard change](../../../Changes/Commands/ExternalDocumentGuard.md) and
[process coverage](../../../../tests/convert/Commands/Metadata/CliSidecarTests.py).
