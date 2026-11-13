# Pinned research corpus

## Purpose

A02 supplies reproducible SOLIDWORKS and Fusion research inputs for the [automation plan](AutomationPlan.md).
All implementation and current-step progress are tracked on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).
The inventory tool reads Git objects, hashes their unchanged bytes and indexes recorded evidence.
It does not decode CAD, convert files, run models or start applications.

**A02 is active, with capture qualification blocked.**
The inventory and authoring specifications are implemented.
Independently authored matched captures and exact-source measurement receipts are still missing.
No conversion capability is established by this inventory.
A03–A16 have not started through this change.

## Pinned inputs

The [manifest](../../../re/automation/Corpus.json) pins commit `74a0bc353421c25f7a6c539897baadf593a05766`.
`.gitattributes` marks the manifest as generated, so GitHub collapses it in pull request diffs.
It contains 1,012 assets: 778 native files, 232 JSON evidence files and two historical corpus notes.

| Native format | Files |
| ------------- | ----: |
| F3D           |   713 |
| F3Z           |     1 |
| SLDPRT        |    58 |
| SLDASM        |     6 |

Each asset records its repository path, Git object ID, SHA-256, byte count and first 16 bytes in hexadecimal.
The prefix is recorded evidence; it is not a container-validity assertion.
The snapshot includes tracked native files under `re/`, Fusion `ground_truth.json` files, SOLIDWORKS measurement JSON, the historical census and corpus notes.
It excludes untracked scratch files, vendor binaries, donor-stream fixtures and other native formats.

The evidence index retains 2,961 recorded measurement fields and 1,179 native-file references with JSON pointers.
References are taken from string values, list items and member names; `recorded_as` says which.
The 63 census rows keyed by filename are recorded as `member_name` references.
Each relative reference is resolved against the evidence file's directory and every ancestor up to the repository root.
All matching tracked native paths are kept as candidates; 746 references currently have one.
Absolute capture-machine paths are recorded but never resolved.
Values, units embedded in field names, null measurements and failures remain unchanged.
All historical observations remain unqualified.
Relative-path associations identify candidate source files but do not prove that those exact bytes were measured.
Build values are recorded only where the original evidence provides them.

The manifest also binds the exact bytes of [PairSpecs.json](../../../re/automation/PairSpecs.json).
It does not implement the future neutral-document research receipt or change schema `1.0`.

## Use the tool

Before starting, install Git and Python 3.11 or later.
Use a complete repository clone containing the pinned commit.
No Python package installation, CAD installation, credentials or network access is required once the Git objects are present.
Run these commands from the repository root.

1. Verify the recorded snapshot against its pinned Git objects and specification digest:

   ```shell
   python3 re/automation/Corpus.py check --manifest re/automation/Corpus.json
   ```

2. Generate a new snapshot at an explicit full commit SHA, using an unused output path:

   ```shell
   python3 re/automation/Corpus.py snapshot --revision 74a0bc353421c25f7a6c539897baadf593a05766 --manifest /tmp/KitCorpusSnapshot.json
   ```

3. Require qualified pairs at a caller's research gate:

   ```shell
   python3 re/automation/Corpus.py check --manifest re/automation/Corpus.json --require-pairs
   ```

The first command reports the pinned inventory when it agrees with the recorded manifest.
The second command creates a new file and refuses to overwrite an existing destination.
The third command currently returns exit code `2`, because zero independently qualified pairs exist.
This command does not qualify captures; that requires independent application evidence and later integration.

| Exit code | Meaning                                                                   | Required action                                                                                          |
| --------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `0`       | Snapshot created, or pin and specification comparison passed              | Continue within the stated inventory scope                                                               |
| `1`       | Invalid input, unavailable Git object, mismatched manifest or I/O failure | Read stderr; restore the expected objects or review the changed inputs                                   |
| `2`       | Inventory verified but qualified pairs are unavailable                    | Supply independently authored captures and exact-source measurement receipts; keep qualification blocked |

Verification reads committed objects, not current working-file bytes.
A modified or missing checkout file does not change the pinned snapshot.
Use a new committed revision and a new snapshot when selecting changed inputs.
In a shallow clone, fetch the pinned commit before verification.

## Author matched examples

Use the five explicit recipes in [PairSpecs.json](../../../re/automation/PairSpecs.json).
Author each source independently in SOLIDWORKS and Fusion.
A converted output is not an independently authored source.
Null capture slots indicate missing evidence; they are not fixture filenames.

| Profile | Design                                                        | Reserved family split          | Baseline expectation                           |
| ------- | ------------------------------------------------------------- | ------------------------------ | ---------------------------------------------- |
| P01     | Constrained 40 × 20 mm rectangle                              | Discovery: rectangular history | Sketch only; no solid body                     |
| P02     | Origin-centered circle, driving diameter 10 mm                | Qualification: circular sketch | Sketch only; retain diameter binding           |
| P03     | P01 extruded 10 mm in +Z                                      | Discovery: rectangular history | One body, 8,000 mm³, center `(20,10,5)` mm     |
| P04     | P03 with a centered 10 × 8 × 4 mm blind cut from its top face | Discovery: rectangular history | One body, 7,680 mm³, center `(20,10,4.875)` mm |
| P05     | Annular revolution, radii 2/6 mm, height 12 mm, angle 360°    | Holdout: annular revolution    | One body, `384π` mm³, center `(0,0,6)` mm      |

These are analytic expectations, not observed application measurements.
The specification fixes frames, driving parameters, constraints, dependencies, edits and quantity-specific tolerances.
Record actual observations separately and compare them against these expectations.
P01 and P02 have no solid volume or center of mass; do not turn absent solid measurements into zero-valued successes.

For each recipe:

1. Record the exact application build, recipe digest, units, frame and native file hash.
2. Rebuild the unchanged design and capture the full feature, sketch, constraint and parameter relationships.
3. Change each independent driving parameter, rebuild, measure and restore it before the next edit.
4. Save and reopen in a fresh process; record healthy controls before and after the measured session.
5. Capture repeated unchanged saves and separately labelled direction, plane, unit and termination variants where applicable.

A08 will integrate isolated sample workers.
This step does not invoke vendor applications or implement worker transport.
Unsupported variants remain distinct from the initial qualified profile.

## Holdout boundaries

Keep a whole family, its authoring lineage, repeated saves and descendants in one split.
P01, P03 and P04 share a rectangular-history family and remain together.
The annular-revolution family is reserved for holdout evaluation.
Do not use holdout captures to fit the rules being evaluated.

Existing imported-study files are reserved for discovery.
The complete SOLIDWORKS V8 project and Fusion external-example group are reserved as holdouts.
Unclassified lineages are quarantined.
If byte-identical native files connect different reserved splits, the tool quarantines the entire affected lineages, including connected duplicate groups.
Connections pass through quarantined lineages, but a duplicate shared only with a quarantined lineage leaves the reserved lineage in place.
These reservations do not prove independent authorship or prevent all semantic near-duplicates.
Audit native ancestry and independent authoring before using any reserved group to claim generalization.

## Verification and remaining work

The snapshot was generated from Git objects without importing the SDK or running CAD.
Only source inspection and permitted static formatting checks ran locally.
Remote process coverage exercises snapshot creation, verification, hash-tamper rejection and the missing-pair gate against tracked native inputs.
The existing `Verify CI policy and pytest compatibility` job runs it on PRs and merge groups; its CI allowlist registration is unchanged.
Merge-group product acceptance remains separate.

The following items still block the complete A02 exit criterion:

- Independently authored native pairs and controlled variants for the five recipes
- Receipts binding actual measurements, application builds, controls and parameter edits to exact source hashes
- Verified independent native ancestry for qualification and holdout families

Historical scratch-file paths do not establish that the files are available.
See [the evidence-binding gotcha](../../Gotchas/Research/HistoricalMeasurementsWithoutSourceHashes.md).
Remote CI results belong to the exact PR revision; a source inspection is not an executed integration test.
Rendered documentation, reader-task evaluation and full language conformance remain unverified.
