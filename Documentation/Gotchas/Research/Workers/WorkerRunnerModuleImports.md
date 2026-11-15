# Worker runner module imports

## Expectation

A runner launched by its Python file path can import helpers from the repository
because the supervisor uses the repository as its working directory.

## Actual behavior

Python file invocation places the script directory first on the import path.
The supervisor also removes inherited `PYTHONPATH` from the runner environment.
A runner under `tests/Research/Outputs` therefore cannot rely on the working
directory being available for package-qualified helper imports.

## Workaround

Register the runner as `python -m tests.Research.Outputs.OutputRunner` with the
session placeholder as its next argument. Module invocation uses the repository
working directory for package resolution and preserves the scrubbed environment.
The Windows process fixture uses the same invocation pattern.

This was identified through source inspection while extracting the output-file
fixture helper. Static steering, typing and formatting checks passed. Remote
runner execution remains pending.
