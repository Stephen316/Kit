# Refuse unchecked metadata sidecars in CLI conversion

`kit convert` refuses nonempty FreeCAD `external_documents` metadata with an
`ExternalDocuments` error before calling a writer. This applies to root and
embedded assembly documents and to every destination format. `kit decode` and
deterministic research inspection remain available.

The FreeCAD writer materializes these metadata children as companion files.
They are outside the assembly document walk and do not receive the CLI's native
transfer and feature-history qualification. Even parameter-only children remain
unsupported through this metadata route; an independently qualified parent does
not qualify its sidecars. The SDK writer is unchanged.

Remote process cases exercise mesh-only, history-free sketch, and parameter-only
children against JSON and FCStd destinations, with root/nested parents and
absent/existing outputs. They require source, destination, and companion-file
preservation plus successful inspection. No local tests or decoding ran. Static
formatting, typing, rationale, path, and whitespace evidence is recorded in PR #119;
process results require its exact-head CI.

See [the sidecar gotcha](../../Gotchas/Conversion/Commands/MetadataSidecarsBypassDocumentWalk.md).
