# Runtime typing imports during discovery

A typing decorator can appear harmless when the development environment already contains `typing_extensions`. Registering Fusion makes its codec imports part of every public registry discovery, including clean wheel installs. The Python 3.11 release smoke environment installs the wheel with `--no-deps`, so the runtime import prevented the entire registry from loading.

The feature sink now configures the shared sink's cumulative byte limit through its constructor and inherits byte emission directly. This preserves the 16 MiB feature limit without any runtime typing backport. Keep development-only type tooling out of production import paths; the isolated wheel and runtime boundaries verify the real import graph.

Evidence: [failed clean-wheel import](https://github.com/TryUniCAD/Kit/actions/runs/43250136029).
