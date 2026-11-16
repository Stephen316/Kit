# Runtime research paths are not static import paths

## Expectation

A test that adds `re/automation` to `sys.path` can share its authored research fixtures with runtime and static checks.

## Observed behavior

The runtime path insertion permits Python to import `FreeCadTwoLengthReadiness`.
The normal project Pyright configuration does not use that insertion as an additional source lookup path.
A bare import therefore produced unresolved-import and dependent type errors in the new FreeCAD process coverage.

## Workaround

Load the fixed repository source path through `importlib.util`.
Register its module before execution so dataclass metadata can resolve the defining module.
Use narrow typed export bindings for the source functions consumed by the test.
Keep the historical controls and their source file unchanged.

The [FreeCAD process coverage](../../../../tests/Research/Archives/FreeCadTwoLengthBindingTests.py) uses this boundary without project path changes, ignores, stubs or duplicated fixture algorithms.
Normal-configuration Pyright and Mypy checks passed after the change.
Local tests, collection and source commands were not executed.
