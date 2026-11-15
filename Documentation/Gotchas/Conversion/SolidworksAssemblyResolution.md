# Cached assembly meshes do not establish loaded component sources

An isolated SOLIDWORKS assembly can retain component display meshes and original
source paths while none of its external component documents are available.
Previously its part definitions exposed those paths without an explicit loaded
source flag. Reads with an empty component file index also returned no
missing-source diagnostics, so path or diagnostic checks could miss the gap.

Definitions now record `attributes.source_resolved`: the decoded root is true;
other definitions are true only when their referenced document was actually
loaded. Cached meshes do not change false to true. Source paths remain provenance
and are not used to infer missing sources in constructed typed JSON documents.
When `resolve_components=False` deliberately defers loading, the adapter omits
the boolean flag on all definitions. Skipped non-root definitions instead carry
`source_resolution: deferred`; the decoded root does not. This explicit marker
retains the missing qualification evidence even when a cached mesh exists,
without falsely reporting that a lookup was attempted and failed. The CLI
refuses the deferred marker recursively, while SDK inspection remains available.
Nested assembly reads use this existing deferred policy; no recursive hydration
is introduced here.

Use `kit decode` to inspect these documents. The CLI conversion guard rejects
explicit false flags, including within nested documents, while SDK inspection
remains available. This evidence does not establish recovered feature semantics
or target-application acceptance.
An unrepresented part or reference is still refused by CLI conversion even
without a false flag. A complete file tree alone does not make a partial nested
neutral projection conversion-ready.

See [the adapter](../../../src/convert/adapters/solidworks/core/Adapter.py),
[the change entry](../../Changes/Solidworks/AssemblyResolutionEvidence.md), and
[CLI process coverage](../../../tests/convert/Commands/CliAssemblyTests.py).
