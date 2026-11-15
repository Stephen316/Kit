# Plugin entry points do not install commands

A package entry-point group named `kit` can look like an installed command declaration.
That group advertises SDK plugins and does not create an executable.
The CLI requires the separate `[project.scripts]` declaration in [package metadata](../../../pyproject.toml).

Older published wheels can expose the `kit` plugin group without providing the `kit` command.
Install a revision containing the console script before following the [CLI procedure](../../Tasks/CommandLine.md).
Use `python -m convert` with that same revision when a shell cannot locate the tool executable.

The installed-metadata and wheel checks verify both groups independently.
See the [packaging entry-point specification](https://packaging.python.org/en/latest/specifications/entry-points/).
