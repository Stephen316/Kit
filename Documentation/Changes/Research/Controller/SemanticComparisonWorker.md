# Semantic comparison controller worker

The `semantic.compare` worker executes the [portable semantic comparator](../../../Reference/Research/SemanticComparison.md) through the existing version 1 single-job controller session protocol.
It consumes immutable `first`, `second` and `tolerances` inputs from the session's content-addressed input directory.
Every descriptor must contain a lowercase SHA-256, its exact `inputs/<sha256>` path and its controller binding.
The worker verifies the normalized job definition and reconstructs the controller snapshot fingerprint before opening the pinned inputs.

The job requires exactly these options:

```json
{
  "scope": "authored-comparison",
  "first_geometry_unit": "mm",
  "second_geometry_unit": "in",
  "max_candidates": 20000
}
```

Geometry units are explicitly `mm`, `cm`, `m`, `in` or `ft`.
The separately pinned tolerance input must declare all five absolute quantities: `length_mm`, `angle_rad`, `dimensionless`, `area_mm2` and `volume_mm3`.
The candidate limit must be an integer from 1 through 100,000.
The job's existing `rule_version` and `tool_version` labels are retained as supplied; they are not asserted to be independently verified Git revisions.

Register the worker using the normal runner registry, with the actual supported Python executable and repository path:

```json
{
  "pool": "semantics",
  "argv": [
    "/actual/python",
    "/actual/Kit/re/automation/SemanticComparisonRunner.py",
    "{session}"
  ],
  "result_schema": "/actual/SemanticComparisonResultSchema.json"
}
```

Generate that records schema with `python re/automation/SemanticComparisonRunner.py --schema` before registration.
Submit a normal `semantic.compare` job with the three input bindings, declared options and existing rule/tool version fields.
The existing registry accepts this kind without controller changes.
The controller adapter must support version 1 output artifacts.

The worker writes `work/semantic-report.json` incrementally with a 32 MiB encoded-byte limit and a private temporary file.
The artifact includes all three input seals, source evidence, declared tolerances, correspondence evidence and exact job definition/fingerprint seals.
Its manifest role is `semantic-report`, with the path `semantic-report.json` relative to the session work directory.
The existing controller intake verifies its SHA-256 and size and retains it after session cleanup.

`result.json` contains a small records receipt with the status, pins, fingerprint, report hash and byte count.
It never embeds the full comparison graph into the 1 MiB records protocol.
A successfully recorded observation has controller outcome `completed`, including `different`, `ambiguous`, `unresolved` and `incomplete` comparison statuses.
That outcome means the observation finished; it does not qualify conversion.
Every receipt and report retains `semantic_qualification: unverified`, `native_acceptance: not_established` and `independent_source_inventory: not_supplied`.
Malformed inputs, absent pins, changed bytes, mismatched fingerprints and oversized reports refuse the worker process before a successful receipt.

## Verification evidence

Static syntax, formatting and whitespace checks were performed.
Dedicated coverage under `tests/Research/Archives/Comparison/SemanticRunnerTests.py` invokes the real schema command, controller, supervisor and worker processes.
It binds independently authored documents, checks a report above 1 MiB survives artifact intake and session cleanup, retains input/fingerprint seals, exercises changed dependencies and ambiguity, and refuses a missing tolerance pin.
The existing Archives workflow selection includes this path.
Local tests and collection were not run; hosted process execution remains required.
This step does not run native applications or establish any CAD acceptance criterion.

Stephen316's [private Windows controller operation](https://github.com/TryUniCAD/Kit/pull/94#issuecomment-6927190826) at `7317092e37f52d6bfc3f26449e2b16a5bd82e86b` completed three strict P03 reader jobs and two comparisons on their first attempts.
The accepted matched-size report SHA-256 `d5b30e651e0e83357e91db48876e845647c0625fa891ba214dc3d32f969eabd4` records `different` with 24 matches.
The deliberate width-edit report SHA-256 `a664d7801d591cc96703bafe017eadeaf4b81f70b688a5784e4635baa00443c5` records `ambiguous` with four ambiguous correspondences.
The operator reopened and hash-checked all five result/receipt pairs and eight artifacts through the controller; the source revision is preserved in this PR's accepted ancestry.
This is an attributed exact-version artifact-custody observation, with private originals retained by the operator.
Current-head hosted checks, independent semantic qualification and native acceptance remain required.
