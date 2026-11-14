# Standalone Fusion adapter imports

The registered Fusion adapter now imports from the installed wheel using Python 3.11's standard library alone. The feature serializer configures the existing metadata sink with its 16 MiB output limit instead of overriding its byte method with a runtime `typing_extensions.override` decorator. The metadata sink keeps its 64 MiB default and rejects non-integer, nonpositive or excessive limits. Both limits still apply cumulatively to every emitted field.

The README format table also lists `.f3d` as registered for reading and writing, matching the public registry while retaining the adjacent qualification limits.

[Release-artifact run 43250136029](https://github.com/TryUniCAD/Kit/actions/runs/43250136029) exposed the undeclared runtime import in the clean Python 3.11 environment. [CI-policy run 43250135711](https://github.com/TryUniCAD/Kit/actions/runs/43250135711) identified the missing README row. The same revision passed all 966 Fusion archive compatibility cases in [run 43250135579](https://github.com/TryUniCAD/Kit/actions/runs/43250135579). Those successes do not substitute for the pending repaired release check. No local tests or test-running builds were run.

See the [runtime import gotcha](../../../Gotchas/Conversion/Fusion/Api/FusionRuntimeTypeImports.md) and [public adapter contract](FusionPublicAdapter.md).
