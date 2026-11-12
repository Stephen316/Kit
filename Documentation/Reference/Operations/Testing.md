# Translation verification

## Purpose

This reference separates structural checks, integration evidence, and product acceptance.
Run tests only in remote CI.
Do not run local tests, collection, reproductions, or hooks that execute tests.

## Verification levels

| Evidence                 | What it can establish                              | What it cannot establish alone  |
| ------------------------ | -------------------------------------------------- | ------------------------------- |
| Static and policy checks | Compliance with configured source rules            | Runtime correctness             |
| Integration checks       | Observed behavior across exercised boundaries      | Complete format coverage        |
| Byte comparison          | Identity for the compared bytes                    | Editable cross-format semantics |
| Neutral-model comparison | Agreement for the compared fields                  | Target-application behavior     |
| Vendor oracle            | Measured behavior in a specified application build | Coverage of untested inputs     |

Unit tests are prohibited by repository policy.
Use meaningful integration, compatibility, smoke, end-to-end, and repository policy checks.

## PR and queue evidence

PR checks cover the configured static and policy scope.
The workflow quality job checks README API examples and format claims on PRs and pushes to `main`.
The merge queue runs heavy acceptance and security checks on its candidate revision.
A green PR acceptance check can record deferral.
It does not mean that the heavy candidate checks ran.
See [merge queue operations](../../../MergeQueue.md).

## Acceptance record

For each source-to-target case, record these items:

- Source and output hashes.
- Kit source revision and options.
- Source and target application versions.
- Required capabilities and transfer results.
- Body count, volume, center of mass, and units.
- Comparison tolerances and their basis.
- Feature tree correspondence.
- Driving-dimension edit and rebuild result.
- Assembly and constraint behavior when applicable.
- Control results before and after the oracle batch.

Do not use one universal tolerance for every quantity and format.
Select and justify tolerances before evaluating the candidate.
Record absolute and relative criteria where the comparison requires both.

## Oracle controls

Use a fresh vendor process for each candidate.
Measure known control documents before and after the batch.
If a control fails, discard the affected batch as acceptance evidence.
A failed environment can produce misleading candidate failures or apparent passes.

Oracle execution remains outside production conversion.
The converter must generate the same output without the vendor runtime present.

## Coverage design

Use source documents that exercise the claimed feature families and configurations.
Include real boundary cases, such as missing references and unsupported constructs.
A roundtrip within one format does not replace cross-format cases.
A synthetic fixture does not represent every real-world source version.

## Research confidence

| Status    | Required evidence                                                                           |
| --------- | ------------------------------------------------------------------------------------------- |
| Confirmed | The rule is decompiled and reproduces a real traced span, corpus record, or measured number |
| Partial   | The rule is decompiled, but no available observation exercises it                           |
| Not found | The rule has not been found                                                                 |

Keep research confidence separate from product acceptance.
A confirmed record field does not establish a complete translator.

## Sources

- [Repository instructions](../../../AGENTS.md)
- [Integration suites](../../../tests/convert/)
- [Research methodology](../../../re/Methodology.md)
- [Oracle evidence](../Research/Oracles.md)
