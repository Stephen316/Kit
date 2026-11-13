# A02 pinned research corpus and paired specifications

## Behavior

Adds isolated research tooling under `re/automation/` to pin committed SOLIDWORKS/Fusion inputs and recorded evidence.
The initial manifest selects commit `74a0bc353421c25f7a6c539897baadf593a05766`: 778 native files, 232 JSON evidence files and two historical notes.
It records source hashes, byte counts, provisional lineage splits, original measurements, native references and missing exact-source bindings.
Five paired authoring specifications define initial sketch, extrusion, cut and revolution cases with controlled edits and family holdouts.

## Usage and limits

Follow [the corpus guide](../../Reference/Research/PinnedCorpus.md).
`Corpus.py snapshot` creates an unused destination from an explicit full Git commit.
`Corpus.py check` compares the manifest with pinned objects and the exact specification bytes.
`--require-pairs` returns `2` while independent qualified pairs are missing.
The tool does not qualify captures, decode CAD, run models, launch applications or change the neutral schema.

**A02 remains active, with capture qualification blocked.**
No matched native pair, conversion support or vendor acceptance is claimed.
The [historical-measurement gotcha](../../Gotchas/Research/HistoricalMeasurementsWithoutSourceHashes.md) records the evidence gap.

## Verification evidence

The initial snapshot was generated directly from Git objects.
Prettier 3.6.2 and Black 26.10.1 checks passed on the applicable changed files.
Python syntax, local Markdown targets and Git whitespace were inspected without importing the SDK.
No local tests, SDK execution or application experiments ran.
Remote process coverage is added for real-repository snapshot creation, verification, tamper rejection and the missing-pair gate.
The [consolidated PR verification job](https://github.com/TryUniCAD/Kit/actions/runs/43419522392/job/131865721189) passed pinned-object verification and all three process cases at `0dd47cdab9d51d24b87acae61ffb1f174ba44d81`.
The registered workflow-quality job runs the coverage; current-head results and current-step progress are recorded directly on [PR #94](https://github.com/TryUniCAD/Kit/pull/94).
Product acceptance remains a separate merge-group requirement.
Source-only documentation review does not establish rendered usability or full language conformance.
