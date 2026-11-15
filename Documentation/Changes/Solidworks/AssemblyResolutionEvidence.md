# Explicit SOLIDWORKS assembly source evidence

SOLIDWORKS assembly component definitions now include the boolean attribute
`source_resolved`. It is true for the root definition decoded from the assembly
and for a component whose document was actually loaded. It is false for every
other unloaded component, including components with cached display meshes.
The attribute is emitted only when component resolution was enabled. A deliberate
`resolve_components=False` read omits it instead of reporting deferred component
loads as failed. Each skipped non-root definition instead records
`source_resolution: deferred`, including definitions with cached display meshes.
The decoded root is not marked deferred. This preserves explicit incomplete
source evidence for nested projections without claiming a failed lookup.
`AsmDefinitions` defaults to enabled resolution for existing
callers; the assembly reader passes its actual resolution setting explicitly.

`source_path` remains provenance. A cached mesh, source filename, or local
instance graph does not prove that an external component document was loaded.
The attribute also records missing sources when reading bytes without a component
file index; this path previously returned no missing-source diagnostics.

SDK readers continue returning inspection documents. No source lookup, geometry,
decoding, or resolution policy changes. The existing CLI conversion guard refuses
explicit `source_resolved: false` evidence at the root and in nested documents.
Use `kit decode` to inspect missing components and the retained cached data.

Actual subprocess coverage copies a native assembly without companion files,
checks root/child evidence in the decode report, and verifies conversion refusal
with source and destination preservation. Existing root/nested JSON cases cover
the same explicit false attribute independently of native decoding.
The native fixture uses partial decoding for inspection and can encounter an
earlier strict-read or opaque-record refusal during conversion. It does not
claim that the false-attribute guard is the sole native refusal reason.
An additional real subprocess invokes the native SDK adapter with resolution
deliberately disabled and verifies that every source-resolution flag is absent.
It also verifies the deferred marker on every skipped non-root definition and
its absence on the decoded root. The CLI refuses explicit deferred markers even
when a cached mesh or another retained representation is present; those records
remain available to SDK and CLI inspection.

This change does not recursively hydrate nested assembly projections. Even with
a complete file tree, a returned nested neutral document can still contain an
unrepresented part and remain ineligible for CLI conversion. The explicit
deferred marker records unfinished source loading, not qualification or complete
component semantics.

No local tests, decoding, or test collection were executed. Pinned formatting,
type analysis and repository steering/path checks cover the change. Remote CI
must execute the process cases; no native acceptance result is claimed.
See [the missing-source gotcha](../../Gotchas/Conversion/SolidworksAssemblyResolution.md).
