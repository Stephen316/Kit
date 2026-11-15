# Semantic checks and inferred writer selection

## Expectation

A partial Fusion history reports the same refusal for explicit format names and suffix-inferred destinations.

## Actual behavior

The registry first resolves an adapter, then checks required semantics before invoking its writer. Explicit `fusion.f3d` and `f3d` names find the registered adapter and the native feature kind is refused before its destination-support check. Inferred `.f3d` selection finds no supporting writer and raises `AdapterNotFoundError` before reaching the semantic guard. Neither path publishes output.

The [Fusion run at `95b3f2e4`](https://github.com/TryUniCAD/Kit/actions/runs/43674626437/job/132691958526) passed 2,958 cases and failed the old explicit-format expectation. The [run at `7e6243b2`](https://github.com/TryUniCAD/Kit/actions/runs/43677583852/job/132701052081) passed 2,959 with three existing skips and failed the replacement case because it incorrectly applied explicit-adapter ordering to inferred selection. No production guard bypass was observed.

## Workaround

Keep actual-history semantic refusal for both explicit Fusion names. Retain exact missing-writer refusal for its inferred Fusion destination, and independently require semantic refusal through an inferred JSON destination whose writer exists. All destinations must remain absent. The separate typed cuboid case retains all three missing-writer checks. The [full Fusion run at `22a59e68`](https://github.com/TryUniCAD/Kit/actions/runs/43678423837/job/132703567976) passed all 2,960 cases with three existing drawing-example skips, including this repaired ordering coverage. Current-head review and native conversion acceptance remain separate.
See [native semantic write qualification](../../../Changes/Research/Readers/NativeSemanticWriteQualification.md).
