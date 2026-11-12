# Black and leading whitespace

Removing a leading comment block can leave an empty first line. Black rejects
that line even when the Python statements are unchanged. Format the affected
files with the version pinned in `pyproject.toml`. See [the formatting
failure](https://github.com/TryUniCAD/Kit/actions/runs/43179663029/job/131052282485).
