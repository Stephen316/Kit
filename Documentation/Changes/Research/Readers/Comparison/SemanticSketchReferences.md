# Declared sketch reference steps

The graph comparator and independent reader evidence inventory now recognize a definition-free timeline reference to a declared sketch.
The strict Fusion rectangle projection already emits this representation before its consuming extrusion.
It uses the reference feature kind, no operation, a sketch link and no operation definition.
That relationship does not require an additional synthetic feature definition.

Recognition requires an actual root timeline `FeatureStep`, reference kind, an explicitly absent operation and definition, and a nonempty sketch identity that resolves uniquely to a root typed `Sketch`.
Supported enum aliases and the model's raw `reference` spelling remain valid.
The graph retains the sketch link and downstream feature dependency and records the classification as an observation.
The evidence inventory accepts only canonical root `CadDocument`, source and tuple collection shapes for this classification.
Nested metadata sketches or feature records cannot stand in for root declarations.
Its declaration inventory is collected inside the existing 200,000-entry evidence visitor, without a preliminary traversal or changed budget.

Unknown or operation-bearing feature kinds, missing targets and duplicated targets retain their missing-definition diagnostics or existing validation refusal.
Malformed root shapes do not gain the exemption.
No adapter, codec, shared model validator, worker protocol or implementation seal is changed.
All native-only data, diagnostics, source extensions and unrelated unresolved evidence remain intact.
Every report retains unverified qualification and unavailable native acceptance.

## Verification evidence

Dedicated process coverage seals independently authored neutral documents and invokes the real graph comparison command and the independent reader evidence component in child processes.
It covers valid enum/raw reference kinds, operation-bearing and unknown steps, absent/dangling/duplicate targets, malformed roots and nested metadata records.
An additional real `reader.neutral` controller scenario uses the tracked P03 Fusion capture with explicitly chosen strict options and inspects its durable reader evidence artifact.
The narrow missing-definition diagnostic must disappear while unrelated evidence and unverified qualification remain.
Static format, syntax, type and steering checks were performed.
No local tests, collection, SDK commands, worker runs or native application execution were performed.
Hosted process verification and independent CAD acceptance remain required.
