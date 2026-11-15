# Reject opaque records in CLI conversion

## Behavior and usage

`kit convert SOURCE DESTINATION` now checks the document returned by its selected
SDK reader before invoking the writer. It refuses `NativeFeature` definitions
and `NativeGeometry` sketch entities in the root or any nested assembly document.
It also refuses PR #94's `kit.research_read_status: unqualified` metadata, including on nested components, even when the installed SDK predates that safeguard.
Every retained `BrepPayload` record is refused, regardless of role, format ID,
or whether its bytes are inline. A payload's preservation or verification tag
does not establish portable semantics. Explicit `NativeCurve`, `NativePcurve`,
and `NativeSurface` records in typed B-rep models are refused as well.
Assembly conversion also refuses native component definitions, missing external
or reference links without embedded documents or local body/mesh representations,
explicitly unresolved source/transform flags, and native-only or unresolved
transform/constraint status. A reference with a complete embedded or local typed
representation is not refused merely because its kind is `reference`.
Both `part` and `reference` definitions require an embedded document, local
body/mesh links, or a local child-instance graph. An unrepresented part is
refused independently of its source path or resolution metadata. Empty local
`assembly` definitions remain eligible; source paths remain provenance.
Definitions that own local child instances also have an assembly representation,
so root and subassembly `source_path` provenance remains valid. Each descendant
is checked independently; owning a local graph does not waive missing-reference
or explicit unresolved/native-only checks. Owner IDs are collected once per
assembly, preserving linear traversal cost.
These records preserve vendor payloads whose portable semantics are still unknown.
Serializing them as interchange JSON does not make them conversion-ready.

Use `kit decode SOURCE` or the deterministic `kit research` commands to inspect
these files and continue reverse-engineering work. Inspection output and the
research document/receipt contract remain available. The guard changes only the
user-facing conversion command; public SDK read and write behavior is unchanged.

The CLI selects and reads the source once, checks it, then uses the public SDK
writer. Strict reading, configuration selection, explicit format selection,
carrier refusal, source protection, and overwrite behavior remain enforced.
Reports retain the selected reader's source identity and the actual writer's
destination identity, including JSON inputs carrying original vendor provenance.
Refusal exits with status 1 and leaves missing or existing destinations untouched.

This guard addresses explicit opaque records. A passing conversion still requires
all applicable native-loadability, editable-history, lossless-conversion, and
target-application acceptance evidence; it establishes none of those by itself.
See [the CLI procedure](../../Tasks/CommandLine.md) and
[the opaque JSON gotcha](../../Gotchas/Conversion/Commands/InterchangePreservesOpaqueRecords.md).
Native CATProduct files can retain complete container bytes while their component
sources, positions, and constraints remain unresolved. See
[the retained assembly gotcha](../../Gotchas/Conversion/Commands/RetainedNativeAssemblyPayloads.md).

## Verification

Native inspection assertions reconstruct typed documents rather than treating [wire tuple tags](../../Gotchas/Ci/TypedDocumentWireTuples.md) as plain arrays.

Source paths alone are treated as provenance, including on typed leaf definitions.
Unrepresented reference kinds and explicit unresolved markers retain refusal; process cases separately cover provenance-only success and marked external-source refusal.

No local tests, decoding runs, or CAD applications were executed.
Pinned Black, Pyright, and Mypy checks and the repository steering/path checks
cover the changed source and process cases. Execution evidence belongs to remote
CI on the accepted PR head; no new native acceptance result is claimed here.

Actual subprocess coverage exercises native SOLIDWORKS refusal, root and nested
JSON native-feature/native-geometry and unqualified research-marker refusal, missing and existing destinations,
source preservation, and continued developer decoding. Genuine typed Fusion
cases retain successful JSON conversion, overwrite handling, native round trips,
and selected-adapter report identities. Typed-source cases retain the unsupported
writer and CATPart output-usability policy checks. This is a CLI follow-up repair
for the conversion guard, separate from deterministic research automation.

Additional process cases copy a real CATProduct into an isolated directory
without its companion files. Implicit and explicit format selection must refuse
conversion, preserve source and destination bytes, and still support decoding.
The decode report verifies the fixture has an empty feature timeline, retained
payloads, and missing component documents. Domain-valid JSON cases exercise all
payload roles with inline or absent bytes, opaque B-rep records, and incomplete
assembly records at the root and within component documents. Complete embedded
reference cases remain positive conversion checks. These new cases await remote
execution; pinned formatting, typing, steering, and path checks pass locally.
Root and subassembly provenance cases additionally verify complete JSON
preservation at the root and inside component documents. Missing descendants
still refuse publication for both missing and existing destinations.
Unrepresented-part JSON cases cover absent provenance and resolution markers.
Positive provenance cases retain actual embedded part documents and body links;
empty local assemblies and fully represented two-level assemblies were positive
under this initial guard. Current eligibility follows the stricter
[model history](ParametricModelGuard.md) and [placement](AssemblyPlacementGuard.md)
requirements.
