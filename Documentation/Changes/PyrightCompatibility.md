# Pyright compatibility

## Behavior

Pyright 1.1.414 infers integer results for literal `struct.unpack_from` integer formats.
The Parasolid unsigned readers now return an explicit integer instead of redundant `isinstance` checks.
Existing buffer bounds checks and `None` results for invalid offsets remain unchanged.
No caller configuration change is required.

## Basis

Python's [format table](https://docs.python.org/3/library/struct.html#format-characters) specifies integer results for `H` and `I`.
Explicit conversion also supports analyzers with less precise inferred types.

## Recorded verification

The [original remote job](https://github.com/TryUniCAD/Kit/actions/runs/42888941281/job/130084609266) reported two `reportUnnecessaryIsInstance` errors.
The correction assigned verification to PR CI.
No local tests ran.
This correction does not establish merge-group or vendor-application acceptance.
