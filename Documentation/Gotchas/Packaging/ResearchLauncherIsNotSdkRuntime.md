# Research process access must stay outside the SDK

A command beneath the SDK source tree can appear harmless when it launches only explicit research tools.
The runtime source policy checks every production module, so the former launcher imported a forbidden process module even for a developer-only command.
The merge candidate also flagged its process replacement operation.

Keep the research composition in the separately packaged `Cli/KitCli` developer source root.
The production `convert` and `interchange` packages must never import that composition.
Use `kit research` or `python -m KitCli research`; `python -m convert` intentionally retains only the production commands.
Keep process imports behind explicit research dispatch so normal installed CLI commands also work with process access blocked.

See [the boundary change](../../Changes/Commands/ResearchRuntimeBoundary.md) and [the failed merge candidate](https://github.com/TryUniCAD/Kit/actions/runs/43713089501).
