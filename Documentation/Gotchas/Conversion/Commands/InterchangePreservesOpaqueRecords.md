# Interchange JSON can preserve opaque vendor records

Expecting successful JSON serialization to establish portable feature semantics
is incorrect. `CadDocument` can faithfully retain `NativeFeature` definitions and
`NativeGeometry` sketch entities, including inside assembly component documents.
The JSON reader restores those vendor-specific records without decoding their
unknown behavior. Original vendor provenance can also remain in JSON read through
the `interchange.json` adapter.

Previously, `kit convert` could publish that document as JSON using the JSON
writer's usability result. The CLI now rejects these explicit opaque records
before calling any writer. Existing destinations and source files are preserved.
Use `kit decode` or `kit research` for inspection and deterministic decoding work
until the required semantics are recovered and validated.

The public SDK and research document/receipt contracts are unchanged. The CLI
guard is not evidence of vendor loadability or editable native conversion for
documents that pass it.

See [the guard](../../../../src/convert/Commands/CheckPortable.py),
[process coverage](../../../../tests/Convert/Commands/CliOpaqueTests.py), and
[the change entry](../../../Changes/Commands/OpaqueConversionGuard.md).
