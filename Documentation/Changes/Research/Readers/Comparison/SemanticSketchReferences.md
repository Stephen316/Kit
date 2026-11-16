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

Stephen316 [reported a new private P03 controller replay](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6929061748) from clean source `880bf0bed53f338933e819eb92b423670c8377d8`, tree `407eaae6f70ee25b8241a089ac0205aadfde8277`.
The new store used distinct operational identities and preserved the original `7317092e` run.
Three reader jobs and two dependent comparisons completed on their first attempts in 53.576 seconds, with zero stale or orphaned sessions.
The private verification seal `bbce22525a4b9b635ea7c3f74f81d8d5966c2abcefda305ae4f3f6bc90193ec8` records result, receipt and artifact hashes and dependency selections.

Both Fusion reader inventories and both joined comparisons omitted the false `missing_feature_definition` finding for the declared sketch reference.
The baseline remained `different`, with 24 matches and 103 reference differences, report SHA-256 `8d37362229495e48bd6684f4ab1c8c817783f9b774429c244564b59545391949`.
The width control remained `ambiguous`, with four alternatives and 119 reference differences, report SHA-256 `8e2d39d991127d13bccfb2457dbb17c6eb1d5d3b78abfe0eeadcaabc36e9e346`.
This is an attributed exact-version process observation with private originals retained by the operator, not current-head hosted acceptance or independent semantic qualification.
Native acceptance remains unestablished.
