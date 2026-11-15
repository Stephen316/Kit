# An unanchored research exclusion also matches core directories

The Black configuration uses `force-exclude = "(examples|modules|re)/"`.
The `re/` alternative also matches the end of `core/`, so explicitly passing files in a core directory can report that no Python files exist to format.

For a focused formatting check, override the expression with `--force-exclude '^/(examples|modules|re)/'`.
This anchors exclusions at the repository root and includes the requested core files.
Review the diff because previously skipped baseline formatting can appear outside the repair scope.

The A04c profile repair observed this behavior with Black 26.10.1 and used the anchored override for its changed core files.
The repository-wide formatter configuration remains a separate change.
