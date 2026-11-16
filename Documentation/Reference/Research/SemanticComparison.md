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

## Related information

- [A01 contract audit](NeutralContractAudit.md)
- [A06 implementation and dependencies](AutomationSteps.md)
- [Paired evidence preflight](../../Changes/Research/Controller/PairedEvidenceManifest.md)
- [Comparison change entry](../../Changes/Research/Readers/Comparison/SemanticGraphComparison.md)
