# Refuse incomplete feature history in CLI conversion

`kit convert` refuses feature steps without definitions, native or imported feature kinds, and unknown feature kinds before publishing output.
A known reference step may omit its definition when it links an existing sketch.
This preserves the supported Fusion circle and rectangle sketch histories.
Such a reference step cannot serve as a design body's final feature.

Each local design body's final feature must be a typed non-reference generator.
That generator and all its transitive feature dependencies must be active in feature-order sequence.
Global feature suppression, per-feature configuration-state suppression, and configuration suppression lists make a step inactive.
The policy treats suppression in any configuration conservatively because the model does not link a separate body result to each variant.
It validates feature kinds and definitions even for inactive steps.
Definitions must match an explicitly supported feature-kind contract; unmapped definitions remain inspection-only.
Profile creation uses `DistanceExtrude`, `PlaneExtrude`, `AngularRevolve`, or `PlaneRevolve` with the existing SDK definition validators.
It requires explicit create intent, an unsuppressed local sketch with nonempty declared profiles referencing nonconstruction entities, and an active declared reference input for that sketch.
Profile links are indexed once per document; this is not geometric profile evaluation.
The structurally understood dependent modifier is `BoundScale`; it reuses the SDK's bound-control validation and requires an active generative input.
Those prerequisites do not qualify its evaluated geometry; local geometry also requires the [SDK regeneration contract](SdkGeometryContract.md).
Legacy fillet, chamfer, shell, hole, pattern, scale, extrusion, and revolution definitions without these concrete prerequisite validators remain inspection-only.
Boolean combine requires at least two distinct active generative inputs and join, cut, or intersect intent; repeated operands and sketch references do not count as generated bodies.
An unrelated suppressed sketch reference without local geometry remains eligible, and tuple storage order does not replace explicit feature order.
Every B-rep body must link through `design_body_id` to one of those local design bodies, and the B-rep body table must be nonempty.
An unrelated typed feature or sketch-only timeline does not establish a generator for unlinked geometry.
Mesh conversion is refused even alongside a typed extrusion because the mesh schema has no typed feature or design-body ownership link.
Provenance and free-form attributes that claim ownership do not replace that missing contract.
Existing document validation checks that body final-feature IDs and sketch links resolve; the CLI adds these representation checks.
Explicit opaque feature, geometry, payload, assembly, and B-rep diagnostics retain precedence.
Parameters without geometry and assembly roots whose typed geometry lives in child documents retain their existing behavior.

The CLI's positive assembly fixtures now embed an actual typed Fusion extrusion document.
Their component definition and document identities remain stable, and their body links follow the embedded typed body.
The shared neutral fixtures are unchanged.

Process cases cover root and nested definitionless extrusion bodies, native, imported, and unknown kind labels with or without typed definitions, bare reference labels, reference final-body steps, and typed B-rep or mesh with only sketch history.
Further cases retain a typed extrusion while adding plain or ownership-tagged meshes, or clearing B-rep body ownership links.
Active-history cases cover suppressed final operations, configuration-state and configuration-record suppression, suppressed direct and transitive dependencies, and root/nested documents with missing or existing destinations.
Positive process cases preserve an unrelated inactive sketch reference and a valid typed extrusion whose timeline tuple is stored in reverse feature order.
Prerequisite process cases add inputless, single-input, repeated-input, reference-only, inactive-input, and invalid-operation boolean records; inputless fillet/scale and reference-only shell records; mismatched kinds; absent profile dependencies; empty, unknown, construction-only, or suppressed profiles; and unvalidated legacy creation definitions.
The former two-generator Boolean serialization case now verifies geometry refusal, alongside a coincident-input cut with a retained nonempty B-rep.
It is retained as regression coverage rather than treating declared operands as evaluated geometry.
They validate input records before invoking the installed CLI, preserve sources and missing or existing destinations, and retain inspection.
Initial positive cases preserved standalone and nested circle and rectangle sketches.
Current eligibility follows the stricter [dimension and model history](ParametricModelGuard.md)
and [assembly placement](AssemblyPlacementGuard.md) guards. Native roundtrip coverage
uses a dimension-driven constrained cuboid.

These checks identify missing or explicit unsupported representations.
Typed definitions and generators do not establish losslessness, live parametric behavior, native loadability, or target-application acceptance.
No tests, decoding, or CAD applications ran locally.
Pinned Black and Prettier formatting passed.
The initial guard's seven Python files passed Pyright, mypy, and steering compliance.
Its ownership regression extension passed the same static checks for all three changed Python files.
The active-history extension passed the same checks for its two new process-fixture files.
The prerequisite repair passed anchored Black formatting, Pyright with zero errors, mypy, and steering compliance for all 12 changed Python files.
Its maintained Markdown passed Prettier; tracked-tree path policy and staged whitespace checks passed.
Remote [CLI job 132657682013](https://github.com/TryUniCAD/Kit/actions/runs/43663480845/job/132657682013) at `3bcfe9fd` reported 12 failed fixtures and 341 passing cases.
All failures were the native/imported/unknown defined-kind fixtures: the SDK rejected their distance-extrusion kind before the CLI ran.
Those cases now use a concrete generic Boolean definition to reach the CLI kind check; this is a fixture correction, not evidence of a production conversion failure.
Pyright also reported three unsupported settings already present in the repository configuration.
Tracked-tree path policy and staged whitespace checks passed; remote process evidence remains required.

See [command usage](../../Tasks/CommandLine.md) and [the definitionless-history gotcha](../../Gotchas/Conversion/Commands/DefinitionlessFeatureHistory.md).
See [typed fixture validation](../../Gotchas/Conversion/Commands/TypedFeatureFixtureValidation.md) for the remote failure and repair boundary.
