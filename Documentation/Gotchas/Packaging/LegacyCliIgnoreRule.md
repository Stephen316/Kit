# A legacy ignore rule covers the CLI package on macOS

The new `Cli/KitCli` source root can appear as ordinary untracked Python files.
The repository's inherited `/cli/*` ignore rule also matches it on a filesystem where Git ignores case.
Ignoring the package would omit its sources from commits and distribution builds.

Keep narrow exceptions for the authored `Cli/KitCli` package and its Python modules immediately after the legacy rule.
Do not force-add ignored files or remove the unrelated ignore rule.
The SDK source roots remain unchanged.
