# Aggregate Fusion outcomes do not identify per-file changes

## Expectation

Unchanged strict, partial, and rejected totals can appear to prove that the Fusion reader handles the same inputs.

## Actual behavior

The [remote corpus job](https://github.com/TryUniCAD/Kit/actions/runs/43656612973/job/132636421153) printed aggregate outcomes only.
Its temporary per-file summaries were removed before artifact publication.
Two files can exchange outcome classes without changing any aggregate total.
The recorded totals therefore cannot reconstruct an exact per-file baseline.

## Workaround

Retain the complete [outcome census](../../Changes/Research/FusionReaderOutcomeCensus.md) before temporary reader output is removed.
Review and commit the report from a named remote revision.
Compare every pinned path, input digest, outcome mode, and rejection reason on later runs.
Record improvements for review instead of silently accepting them.
Keep semantic qualification and native acceptance as separate evidence gates.
