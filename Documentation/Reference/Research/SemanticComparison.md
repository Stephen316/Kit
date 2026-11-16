# Compare portable semantic graphs

## Purpose

Use the A06 research comparator to compare two existing `CadDocument` JSON documents without relying on names or native identifiers.
The tool reports correspondence candidates, observed differences and unresolved domains.
It does not qualify a reader, writer or native conversion.

## Before you start

Use the repository's supported Python environment and a checkout containing the interchange codec.
Obtain two JSON documents from the existing codec.
Record their exact SHA-256 values independently.
Determine each document's geometry units from its source contract.
The document's display-unit field alone does not establish the coordinate convention.

Write a tolerance JSON file with exactly these five nonnegative absolute limits.
Choose the values before evaluating the pair.
These example limits are explicit choices, not measured native acceptance evidence.

```json
{
  "length_mm": 0.000001,
  "angle_rad": 0.000000001,
  "dimensionless": 0.000000001,
  "area_mm2": 0.000001,
  "volume_mm3": 0.000001
}
```

Record that file's SHA-256.
No relative tolerance or implicit global epsilon is applied.
Counts, booleans and exact fields remain exact.
Dimensionless integer controls remain exact even when a floating tolerance is nonzero.
Normalized quantity atoms retain reduced exact ratios alongside their displayed numeric values.

## Procedure

Run the command with your actual paths, independently recorded hashes and declared geometry units.
The uppercase hash values below are user-supplied placeholders.

```sh
python3 re/automation/SemanticComparison.py \
  --first /private/pair/First.json --first-sha256 FIRST_SHA256 \
  --first-geometry-unit mm \
  --second /private/pair/Second.json --second-sha256 SECOND_SHA256 \
  --second-geometry-unit in \
  --tolerances /private/pair/Tolerances.json \
  --tolerances-sha256 TOLERANCES_SHA256
```

Geometry units can be `mm`, `cm`, `m`, `in` or `ft`.
Typed length parameters retain their own unit conversion.
Typed angles accept `rad` or `deg` and normalize to radians.
The report retains the original unit observations and source identity digests.

The default candidate budget is 20,000 evaluations.
Use `--max-candidates` to select a value from 1 through 100,000.
An exhausted candidate or evidence budget cannot produce an equality success.

## Expected result

The command prints a JSON report with the pinned inputs, comparison status, source issues and explicit correspondence evidence.
The report seals the three comparison source files and refuses source changes during an evaluation.
Matched records retain both source identities and field paths.
Ambiguous entries retain their alternatives and scores.
Dependency differences retain reference roles, endpoints and multiplicities.
Names and collection traversal order do not select a counterpart.

| Exit | Status                                    | Meaning                                                                                       |
| ---: | ----------------------------------------- | --------------------------------------------------------------------------------------------- |
|    0 | `equal_observed_graph`                    | The compared typed observation graph agrees within the declared limits                        |
|    1 | Refusal on stderr                         | Invalid input, changed pin, unsupported quantity, malformed document or exceeded output limit |
|    2 | `different`                               | The observed fields, records or dependency links differ                                       |
|    3 | `ambiguous`, `unresolved` or `incomplete` | Correspondence, source semantics or bounded work remains unresolved                           |

Every report retains `semantic_qualification: unverified` and `native_acceptance: not_established`.
Reader agreement cannot prove that both readers preserved every required source relationship.
The report does not authorize a writer to remove retained source evidence.

## Limits and failures

Each document is limited to 32 MiB and the tolerance file to 64 KiB.
Inputs must be plain regular files with matching hashes.
Duplicate JSON keys, nonfinite quantities and excessive JSON nesting are refused.
Raw JSON is bounded to depth 64 and 500,000 visited values; the typed semantic walk remains bounded to depth 48.
Decimal literals that lose canonical magnitude in the codec are refused before graph construction.
Distinct wire keys that resolve to the same model slot are refused, including collisions introduced by a registered migration.
Unambiguous compatibility aliases remain valid.
Each projected document has at most 4,096 nodes and 100,000 scalar fields.
Identities are limited to 512 characters.
Individual field text is limited to 65,536 characters.
Candidate evidence has an 8 MiB budget, and the report has a 32 MiB limit.

Unclassified attributes, native-only values, missing feature definitions and reader diagnostics remain explicit issues.
Full B-rep, meshes, payloads and assembly graphs require separate comparison.
Different inline and linked definitions remain different until their driving relationships have independent equivalence evidence.
Constraint operands and closed-profile sequence are preserved.

For a changed pin, restore the intended immutable input or seal a new comparison request.
For ambiguity, obtain distinguishing ownership or relationship evidence.
Do not increase tolerances, remove constraints or mask native fields merely to produce equality.

## Run through the controller

Register [the comparison worker](../../Changes/Research/Controller/SemanticComparisonWorker.md) as `semantic.compare` in an offline pool.
Generate its records schema with `SemanticComparisonRunner.py --schema` using the same supported Python environment as the worker.
Bind both neutral documents and the tolerance file through the existing controller `bind` command.
Submit this job with your actual immutable rule and worker versions:

```json
{
  "id": "compare:pair",
  "kind": "semantic.compare",
  "inputs": {
    "first": "neutral:first",
    "second": "neutral:second",
    "tolerances": "tolerances:pair"
  },
  "rule_version": "ACTUAL_IMMUTABLE_RULE_VERSION",
  "tool_version": "ACTUAL_IMMUTABLE_WORKER_VERSION",
  "options": {
    "scope": "paired-rectangle",
    "first_geometry_unit": "mm",
    "second_geometry_unit": "mm",
    "max_candidates": 20000
  }
}
```

The worker verifies the controller fingerprint and all three byte seals.
It publishes the bounded graph report as the immutable `semantic-report` artifact.
The small records receipt retains the report hash, input hashes and observation status.
This preserves reports above the controller's 1 MiB metadata limit.

A controller outcome of `completed` records that the comparison observation finished.
Inspect its `status`, unresolved domains and qualification fields before using it as evidence.
Differences, ambiguity and exhausted work remain explicit completed observations.
The controller cannot turn an observation receipt into independently qualified CAD semantics.
Update the job's immutable `tool_version` when its implementation changes so the controller invalidates cached work.
The report's source-file seals record the executed observation; they do not automatically update existing job definitions.

## Connect native reader jobs

Register [the native reader worker](../../Changes/Research/Readers/Comparison/NeutralReaderWorker.md) as `reader.neutral` alongside `semantic.compare`.
Generate each worker's records schema and use an adapter that supports durable output artifacts.
Bind the two actual native inputs as `native:first` and `native:second` and bind the tolerance profile as `tolerances:pair`.
Then submit a batch such as the following through `submit-batch`.
Replace the immutable version placeholders and choose read options for the intended observation before scheduling.
The example explicitly chooses partial reads and millimetre geometry contracts; neither choice is inferred from display units.

```json
{
  "jobs": [
    {
      "id": "read:first",
      "kind": "reader.neutral",
      "inputs": { "source": "native:first" },
      "rule_version": "ACTUAL_IMMUTABLE_RULE_VERSION",
      "tool_version": "ACTUAL_IMMUTABLE_WORKER_VERSION",
      "options": {
        "scope": "paired-rectangle",
        "source_format": "fusion.f3d",
        "strict": false,
        "configuration": null
      }
    },
    {
      "id": "read:second",
      "kind": "reader.neutral",
      "inputs": { "source": "native:second" },
      "rule_version": "ACTUAL_IMMUTABLE_RULE_VERSION",
      "tool_version": "ACTUAL_IMMUTABLE_WORKER_VERSION",
      "options": {
        "scope": "paired-rectangle",
        "source_format": "solidworks.sldprt",
        "strict": false,
        "configuration": null
      }
    },
    {
      "id": "compare:pair",
      "kind": "semantic.compare",
      "depends_on": ["read:first", "read:second"],
      "inputs": {
        "first": { "dependency": "read:first", "artifact": "neutral-document" },
        "second": {
          "dependency": "read:second",
          "artifact": "neutral-document"
        },
        "tolerances": "tolerances:pair"
      },
      "rule_version": "ACTUAL_IMMUTABLE_RULE_VERSION",
      "tool_version": "ACTUAL_IMMUTABLE_WORKER_VERSION",
      "options": {
        "scope": "paired-rectangle",
        "first_geometry_unit": "mm",
        "second_geometry_unit": "mm",
        "max_candidates": 20000
      }
    }
  ]
}
```

Each reader preserves its complete codec document, including native payloads, diagnostics and metadata.
Its `reader-evidence` artifact retains unresolved records, raw source seals, exact options and observed implementation hashes.
The comparator consumes the accepted immutable `neutral-document` artifacts through controller dependency selectors.
Changed native bindings, definitions or accepted reader results invalidate the dependent comparison.
No manual neutral export or broad identity mask is inserted between these steps.

Read failures stop the dependent comparison rather than silently changing strictness or dropping source content.
A completed reader observation does not establish portable completeness.
The retained source issues can keep the comparator unresolved, ambiguous or incomplete.
Independent source admission, frozen-rule evaluation and native acceptance remain required.

## Related information

- [A01 contract audit](NeutralContractAudit.md)
- [A06 implementation and dependencies](AutomationSteps.md)
- [Paired evidence preflight](../../Changes/Research/Controller/PairedEvidenceManifest.md)
- [Comparison change entry](../../Changes/Research/Readers/Comparison/SemanticGraphComparison.md)
- [Controller worker contract](../../Changes/Research/Controller/SemanticComparisonWorker.md)
- [Native reader worker contract](../../Changes/Research/Readers/Comparison/NeutralReaderWorker.md)
