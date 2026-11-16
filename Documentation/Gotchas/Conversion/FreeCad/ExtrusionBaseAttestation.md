# Extrusion base ownership differs from history dependencies

A nonempty `input_feature_ids` roster does not establish that FreeCAD will emit a Boolean extrusion result.
`FeatureDataOf` resolves an input base only through entries already recorded in `SolidNames`, then falls back to the current solid.
Sketch-reference and other reference-only steps do not advance that solid state.
Conversely, an earlier solid can become the base even when the new extrusion has no explicit input IDs.
`AddBoolMut` treats omitted operation as Create and converts Create with an existing base to Join.
The adapter's supported inline extrusion predicate also admits omitted operation.

The first attestation repair incorrectly used an empty dependency roster as a proxy for the standalone emitter route and required explicit Create.
That missed a first extrusion with reference dependencies or omitted operation, and could include the first extrusion in a later Boolean history.
The corrected predicate conservatively covers a standalone document whose sole active non-reference step is a supported extrusion with explicit Create or omitted operation and no retained BREP or usable mesh representation.
It retains the actual reference dependencies and leaves both result and metadata qualification flags false.
Real public process controls include a preceding sketch-reference step with `native_type=sketch`, explicit/default Create, and omitted operation without dependencies.
They inspect one native extrusion without a Boolean result, then require the strict public policy to refuse without destination mutation.

Histories with other solid, Boolean, native or imported steps remain outside this scoped audit.
Empty meshes and nonreserved auxiliary or verification notes do not establish geometry and cannot exclude that fresh history from unqualified flags.
The existing `IsNative` predicate protects native-document and native-binding payload routes; other payload roles and actual retained BREP remain a separate audit.
The existing `IsMeshUsable` predicate preserves genuine nondegenerate mesh routes.
Those exclusions do not qualify any retained route: a non-geometric payload container is not initial solid evidence.
Do not infer geometry acceptance from container presence, dependency roster shape or a computed shape cache.
Independent native initial-open measurements remain required.
See [the attestation change entry](../../../Changes/FreeCad/FreeCadInitialGeometryAttestation.md) and [the initial recompute witness](GeneratedExtrusionRequiresRecompute.md).
Local verification was static only; these process controls were not executed locally.
