# Require native transfers for CLI conversion

The writer policy accepts `require_native_transfers` in `WriteOptions.values` or public `WriteDocument` `InputValues`.
The option must be a boolean and defaults to `False`, preserving existing SDK behavior.
When `True`, every reported capability transfer must use native mode.
Both carrier and mixed transfers are refused, including intrinsic target limitations and regardless of `allow_carrier`.

The CLI enables this policy before invoking its selected writer.
The checked write raises the existing `UsabilityError` with the writer's transfer evidence before staged paths or streams are published.
Source files, missing destinations, and existing destinations retain the transactional boundary.
The public SDK keeps its existing target-limitation behavior unless the caller enables the option.
The strict Fusion writer accepts this policy key while retaining its existing option checks.

The process integration fixture uses an actual FreeCAD write of a typed parameter document with two configurations.
FreeCAD reports the configurations as `target_unsupported` carrier transfers.
CLI cases cover missing and existing destinations, source preservation, and absence of staged artifacts.
A separate public SDK subprocess verifies that its default policy still publishes the same FreeCAD target with `AllowCarrier=False` and reports the target limitation.
Archive structure and transfer evidence do not establish native application or parametric acceptance.

No local tests, decoding, or CAD applications ran.
Pinned Black and Prettier formatting passed.
Pyright reported zero errors, mypy reported no issues, and steering compliance passed for all four changed Python files.
Pyright also reported three unsupported settings already present in the repository configuration.
Tracked-tree path policy and staged whitespace checks passed; remote process execution remains required.

See [the target-limitation gotcha](../../Gotchas/Conversion/Commands/TargetGapCarriers.md).
