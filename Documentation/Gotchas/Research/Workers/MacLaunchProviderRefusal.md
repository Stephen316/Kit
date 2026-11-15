# A stopped macOS launch helper may never reach the requested control

## Expectation

A deliberately changed bundle pin or retained fence exercises the corresponding Swift provider guard.

## Actual behavior

The initial fixture accepted a generic failure for both controls. A Swift compile or startup failure would pass those assertions before the provider reached either guard. The positive hosted case reported only the generic failure, leaving its provider cause unresolved. [Initial hosted job](https://github.com/TryUniCAD/Kit/actions/runs/43770822331/job/132986201023)

## Workaround

Check each refusal against its specific return code and reason. Read the bounded stderr excerpt from the disposable fixture when the provider fails unexpectedly. The owner CLI retains its existing generic refusal output for live installations. [Replacement launch procedure](../../../Changes/Research/Workers/FusionReplacementLaunch.md)
