# Separate the installed CLI from research implementation

The user requested a separate CLI PR compatible with PR #94.
This correction removes the installed command, CLI packaging, CLI-only cases, and related guides from PR #94.
The implementation moves to [PR #119](https://github.com/TryUniCAD/Kit/pull/119).
Published history is preserved; this is a normal cleanup commit.

Research readers, controller, supervisor, corpus, export safeguards, native traversal fixes, and capture work remain in PR #94.
The standalone CLI uses a selected research checkout through a separate process.
Its compatibility job exercises a pinned PR #94 revision without importing research modules into conversion.

The Fusion reader guide retains a direct reader command for this checkout.
CLI installation and deterministic command instructions, including agent guidance, belong to the separate CLI PR.
No native acceptance requirement changes.

Source inspection and whitespace/path checks verify the cleanup scope.
Remote CI and native review remain required for the accepted cleanup head; no tests ran locally.
