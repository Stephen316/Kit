# Semantic refusal precedes writer selection

## Expectation

A partial Fusion history with no supported writer raises `AdapterNotFoundError` for an explicit or inferred Fusion destination.

## Actual behavior

The [Fusion compatibility run at `95b3f2e4`](https://github.com/TryUniCAD/Kit/actions/runs/43674626437/job/132691958526) passed 2,958 cases with three existing skips and failed one historical API caller. Its real history read retains an explicit native feature kind. The shared required-semantic guard now refuses that evidence before looking for a writer.
This intentional refusal preserves the destination and does not change successful reader inspection.

## Workaround

Keep the history read and require its native-semantic refusal for both explicit destination spellings and suffix inference. Preserve missing-writer checks separately using the independent typed cuboid with no authoring/native-state metadata contract.
The new split retains both behaviors and absence of output files. Current-head remote execution remains required.
See [native semantic write qualification](../../../Changes/Research/Readers/NativeSemanticWriteQualification.md).
