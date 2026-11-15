# Native semantic write qualification

Public JSON, Fusion, CATIA, FreeCAD, and registry writes now refuse native or unknown feature kinds and unknown boolean operations before output mutation.
The refusal covers component documents and suppressed history.
It does not require every feature to have a definition: explicit reference nodes and independently validated contracts can represent required semantics elsewhere.

## Authoring contract scope

Explicit `native` feature tags remain refused even when metadata claims a Fusion authoring or native-state contract.
The initial exception assumed that low-level authored move, split and paste codec support established a reachable public contract.
The [remote run at `6e2da255`](https://github.com/TryUniCAD/Kit/actions/runs/43673027349/job/132687037643) disproved that assumption: constructing the move fixture failed before the write guard because the existing state allowlist excludes its part-feature types.
The unsupported exception and its encoder import are removed; no state types are admitted to make that fixture pass.

The positive public JSON/Fusion file case uses the existing independently authored cuboid contract.
Separate cases retain graph and version tamper refusal with explicit native tags.
A part-family file is still emitted and read through the existing low-level codec, then its unsupported public state construction is explicitly refused.
That file readback does not qualify public native semantics or application acceptance.
The [part-state gotcha](../../../Gotchas/Conversion/Qualification/NativePartStateAllowlist.md) records the distinction.

## Unresolved assemblies

CATProduct bytes reads can retain component occurrence names while their transforms and constraints remain unresolved.
The reader records `transform_status` and `constraint_status` as `native-only`, and occurrence attributes record `transform_resolved=False`.
Public writes now reject these explicit markers even when component documents are unavailable and the root has no native feature definition.
Changing the source format or persisting the document as interchange JSON does not remove the refusal.
Reading and explicit model serialization remain available for inspection.

## FreeCAD required features

FreeCAD now checks every component history before selecting replay or creating destination and component files.
A required step must pass the existing native feature check or appear in the actual editable feature set produced by the existing emitter.
The latter path applies to standalone part emission, where the writer already enables its edit plans.
Nested paths that do not enable those plans cannot claim their standalone qualification.
Suppression does not establish preserved editable semantics.

Unsupported generic records, missing required extrusion definitions, and unproven open or intersecting extrusion profiles now cause a `ValueError` rather than default geometry or a neutral-only feature carrier.
Extrusion qualification reuses the existing closed-profile, topology, and positive-length checks for every source format.
`allow_carrier=True` and disabled structural validation do not bypass this required-feature check.

When the ordinary native feature check cannot account for a standalone part, the preflight builds an additional candidate archive in memory to obtain the emitter's actual editable IDs.
That candidate is discarded before destination work.
This extra encode scales with the model and retained payloads; the preflight introduces no separate enforced size or memory bound.
Its IDs do not qualify a component path that uses different emission options.

The previous public carrier and replay paths for histories that fail this check are intentionally refused.
Low-level archive construction and explicit model serialization remain available for inspection and research.
Neither path establishes production conversion acceptance.

## Verification evidence

The [remote caller run](https://github.com/TryUniCAD/Kit/actions/runs/43669741073/job/132676916864) exposed three fixture assumptions after the earlier safeguards: a Fusion-derived filtered carrier did not advertise native payload capability, and two neutral FreeCAD profiles produced executable extrusion objects despite missing profile proofs.
The filtering case retains its configuration, source identity, payload filtering, capability equality, and replay assertions with the independent source's actual capabilities.
The open-line and intersecting-circle cases now retain their profile intent and require refusal without destination mutation.
Their valid typed-circle counterpart remains positive.

New integration cases use a real CATProduct bytes read, saved and reopened relabeled interchange inputs, nested documents, all direct writer spellings, and public registry writes.
They require preservation of files and streams and absence of newly created destination directories.
Nested fixtures declare assembly components as assemblies rather than parts.
Positive cases retain independent assembly model serialization, the existing independently authored cuboid contract, and typed FreeCAD part and assembly output.
Generic deterministic-output and stream-probe cases now use a fully specified neutral extrusion.

The shared checks cover explicit unqualified tags, operations, and markers; they do not establish complete definition semantics for every known feature kind.
In particular, a known non-native kind with no definition can remain serializable as interchange JSON while FreeCAD refuses to claim an editable representation for it.
This remaining qualification scope is not native conversion acceptance.

The first installed-wheel gate at `6fb599a9` exposed a shared-guard/Fusion-package import cycle.
The intermediate repair deferred the encoder import until contract evaluation. The final guard removes that dependency along with the unsupported exception above.
The [import-cycle gotcha](../../../Gotchas/Conversion/Qualification/FeatureGuardImportCycle.md) links the actual fresh-interpreter failure.

No local tests, decoding, collection, or application runs verified this change.
Remote integration and current-head review remain required.
Encoding, model equality, and archive readback do not establish native application loadability, editable acceptance, or completion of A11–A15.

See the [FreeCAD guide](../../../Reference/Adapters/Freecad.md), the [assembly marker gotcha](../../../Gotchas/Conversion/Qualification/NativeAssemblyMarkers.md), and the [FreeCAD default-geometry gotcha](../../../Gotchas/Conversion/Qualification/FreecadDefaultGeometry.md).

The broader Fusion run at `95b3f2e4` passed 2,958 cases and exposed one caller expecting writer lookup before native-tag refusal. The repaired cases preserve the actual partial-history refusal and independent typed missing-writer behavior; [the ordering gotcha](../../../Gotchas/Conversion/Qualification/SemanticGuardPrecedesWriterLookup.md) links the failure.
