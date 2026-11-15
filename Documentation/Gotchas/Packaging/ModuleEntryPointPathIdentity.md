# Python module launchers require an exact filename

Moving a CLI into a PascalCase package does not make its module launcher a PascalCase Python filename.
`python -m KitCli` requires the ecosystem-defined `__main__.py` identity.
The repository path checker records these exceptions as exact paths, so the existing SDK module exception does not cover a new package.

Register only `Cli/KitCli/__main__.py` beside `src/convert/__main__.py` in the explicit ecosystem path set.
Keep ordinary package files and neighboring paths subject to the original PascalCase policy.
