# CAD success criteria

## Purpose and authority

This page collects every acceptance condition for CAD work in Kit.
Reading it is mandatory before CAD parsing, writing, conversion, verification, or reverse engineering.
Reading it is also mandatory before any claim that CAD output works.
[AGENTS.md](../../../AGENTS.md) and [CLAUDE.md](../../../CLAUDE.md) make this page required.

The linked standards are the authoritative source.
This page does not relax, shorten, or replace any of them.
If this page and a source standard differ, apply the stricter requirement and correct this page.

| Source                                                                                                                    | Scope                                             |
| ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| [No donor blocks](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md)            | Every emitted byte comes from format knowledge    |
| [No CAD runtime](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoCadRuntime.md)              | CAD applications are oracles only                 |
| [Lossless translation](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/LosslessTranslation.md) | Lossless, loadable, usable, and parametric output |
| [Complete implementations](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/NoStubs.md)         | No stubs, placeholders, or partial delivery       |
| [Fusion donor data ban](../Research/FusionDonorBan.md)                                                                    | Fusion examples of banned and allowed data        |
| [Oracle evidence](../Research/Oracles.md)                                                                                 | Control and measurement sequence                  |
| [Translation verification](Testing.md)                                                                                    | Evidence levels and the acceptance record         |
| [Reverse engineering instruction book](../../../re/Playbook/README.md)                                                    | The required method for format research           |

## The criteria

Every criterion applies at the same time.
A result that fails one criterion fails acceptance.

| ID  | Criterion               | Required condition                                                                                     |
| --- | ----------------------- | ------------------------------------------------------------------------------------------------------ |
| C1  | No donor data           | Zero vendor-saved bytes, rows, templates, or fitted values in `src/`, package data, or writer output   |
| C2  | No CAD runtime          | Conversion runs on a clean machine with no CAD application, SDK, license, service, or plug-in          |
| C3  | Lossless                | Every source feature, sketch, dimension, constraint, plane, origin, body, and geometry item is present |
| C4  | Fully parametric        | The target feature tree is live, and a driving dimension change rebuilds the geometry                  |
| C5  | Vendor loadable         | The target application opens the file without a repair step and without an empty document              |
| C6  | Application usable      | Body count, volume, and center of mass match the source within declared tolerances                     |
| C7  | Measured acceptance     | The target application measured the output in a fresh process between two healthy controls             |
| C8  | Honest attestation      | `vendor_loadable` and `application_usable` are `True` only when C5 and C6 are measured                 |
| C9  | Complete implementation | No stubs, no placeholder values, and no partial output that silently omits a feature                   |
| C10 | Generalization          | Each format rule holds on held-out inputs that did not contribute to the rule                          |
| C11 | Traceable knowledge     | Each emitted field traces to a recorded finding in `re/` with a confidence status                      |

## C1. No donor data

Kit must make every emitted byte from reverse-engineered format knowledge.
The ban covers donor files, donor blocks, generic templates, and fallbacks to donor data.
The ban also covers per-case tables and values that fit one document or one case.
A constant that nobody can explain field by field is donor data.

The following items are allowed in production code:

- Declared format vocabulary, such as class names, schema numbers, enum codes, and field order.
- A proven constant in its smallest form, with the documents that show it and the reason it cannot change.
- Values from the source document when Kit converts that same document.
- Values that Kit computes from the requested model.

The `re/` research tree can keep vendor-saved controls and captured tables.
Production code must never load a file from `re/`, `tests/`, or `examples/`.
A captured table that moves from `re/` into `src/` becomes donor data.

## C2. No CAD runtime

A CAD application can only author samples, inspect semantics, measure output, or supply traces.
Keep that use in isolated research or test tooling.
Production modules must not import an oracle harness.
Production conversion must not launch, attach to, or call a CAD process or service.
The same output bytes must come out when the oracle is absent.
Unsupported input fails explicitly. It never falls back to a CAD application.

## C3. Lossless

The output contains everything that the source contains.
This includes the feature tree, sketches, dimensions, constraints, planes, origin, bodies, and geometry.
It also includes assemblies, mates, configurations, parameters, equations, and drawings when the source has them.
The `dropped` field of the result must be empty.
A carrier that holds neutral Kit data is not lossless output.

## C4. Fully parametric

A parametric source becomes a parametric target.
The feature tree is live in the target application.
Dimensions and parameters drive the geometry.
A rebuild completes without errors.
A dumb solid, a mesh, or baked geometry fails this criterion.

## C5 to C7. Loadable, usable, and measured

Only the target application decides acceptance.
Byte identity, segmentation coverage, decoded-byte percentages, and object counts are instruments only.
They never replace a loaded model.

1. Measure a known control document in the target application.
2. Start a fresh process for the candidate.
3. Open the candidate and record every load error.
4. Rebuild the candidate and record every rebuild error.
5. Record the body count, volume, and center of mass.
6. Record the feature tree node by node.
7. Change a driving dimension and rebuild.
8. Measure the geometry change.
9. Measure the control again.

Expected result: the report contains each number and both control results.
If either control fails, discard the batch.
A file that opens with zero bodies is a failure.
A file that opens to an empty viewport or an empty feature tree is a failure.

## C8. Honest attestation

Set `vendor_loadable` and `application_usable` from measurements only.
Do not remove these flags to make a result look complete.
An honestly attested unusable file is still unfinished work.
State a failure in the first line of a report, with the measured numbers.

## C9. Complete implementation

Do not ship stubs, placeholder values, or mock success.
A file that is missing one feature has silently wrong geometry.
If a writer cannot express every feature, it must refuse the input with a diagnostic.
It must not emit a partial model as a success.

## C10. Generalization

A rule must work for inputs that it was not fitted on.
Test each rule on held-out samples before you promote it.
A table with one entry per case does not scale and is donor data.
A regression or correlation gives a hypothesis only.
Promote a rule when decompiled code or a proven constant explains it.

## C11. Traceable knowledge

Record each finding in `re/` when you make it.
Label each field with the confidence status from the [research method](../Research/Methodology.md#confidence-register).
Record refuted hypotheses as well as confirmed findings.
A partial field is a hypothesis with an address. It is not a fact.

## Results that are not success

The following results are failures, not outcomes:

- A file that opens with zero solid bodies.
- A file that opens with no feature tree, planes, origin, or sketches.
- A carrier that the target application cannot read as native data.
- Baked or mesh geometry from a parametric source.
- `vendor_loadable = False` or `application_usable = False`.
- A partial result with an explanation of why the remaining work is difficult.
- Round-trip byte identity or object counts in place of a loaded model.
- Output that uses donor bytes, a template, or a fallback to recorded data.
- Output that needs a CAD application at conversion time.

## Stopping conditions

There are two acceptable stopping conditions.
The first is success under every criterion on this page.
The second is the end of the available context.
Missing grammar is the work. It is not a blocker.
Do not ask whether to continue reverse engineering.
Identify the blocking stream or field, state the next action, and continue.

## Checklist before a completion claim

1. Scan `src/` for encoded vendor payloads and vendor stream data files.
2. Scan production code for CAD automation imports, process launches, and oracle dependencies.
3. Confirm that installation metadata declares no CAD dependency.
4. Confirm that each emitted field traces to a finding in `re/`.
5. Confirm that each rule passed on held-out samples.
6. Record the oracle results from the procedure in C5 to C7.
7. Compare the feature tree with the source node by node.
8. Confirm the dimension edit and rebuild result.
9. Confirm that `dropped` is empty.
10. Confirm that `vendor_loadable` and `application_usable` are `True` from measurements.

If any check fails, the work is not complete.

## Research exemption

The `re/` tree is exempt from code standards and unit-test requirements.
It is not exempt from these criteria when a result is claimed as product support.
A research experiment can use donors and vendor automation inside `re/`.
Its location does not qualify it for shipping or establish acceptance evidence.

## Related information

- [Reverse engineering instruction book](../../../re/Playbook/README.md)
- [Research method](../Research/Methodology.md)
- [Evaluate a conversion result](../../Tasks/InspectResult.md)
