# Getting started

## Purpose

Use Kit from a Python application.
This guide links the shortest path from installation to result evaluation.
The complete API is in the [API reference](Reference/Overview/ApiReference.md).

## Before you start

Install `uv` and use Python 3.11 or later.
For an application project, follow [published installation](#install-a-published-release) below.
For repository development, follow [repository installation](Tasks/Install.md).
The repository procedure creates an isolated checkout with locked dependencies.
Keep the original CAD file unchanged.
Select an unused output path.

The distribution is `unicad-kit`.
The installed packages are `convert` and `interchange`.
The package metadata does not declare a `kit convert` console command.

## Install a published release

For a separate application project, install a published package from PyPI.
Use Python 3.11 or later.
Run `uv init` first if the project is new.

```sh
uv add unicad-kit
```

If no release is available, use [repository installation](Tasks/Install.md).
Run examples with `uv run python` in the installed application project.
Use the repository instructions when contributing to Kit.
See [release publishing](Changes/CommitReleases.md) for artifact and publication details.

## First conversion

The example requires a real file named `bracket.SLDPRT`.
It requests FreeCAD output at `bracket.FCStd`.
The source content can exceed the implemented feature coverage.

```python
from convert import convert as ConvertDoc

Result = ConvertDoc("bracket.SLDPRT", "bracket.FCStd", allow_carrier=False)
```

Expected result: a `ConversionResult` or an exception that explains the failed boundary.
The destination suffix selects the writer unless `destination_format` is supplied.
Existing destinations are protected by default.

## Evaluate the result

1. Read `Result.output`.
2. Check `Result.application_usable` and `Result.vendor_loadable`.
3. Check `Result.dropped` and `Result.requirements`.
4. Inspect `Result.transfers`.
5. Compare the required vendor evidence with the source.

See [result evaluation](Tasks/InspectResult.md) for the acceptance criteria.
Do not infer lossless output from a return value or a native mode label.

## Choose the next task

| Task                       | Guide                                             |
| -------------------------- | ------------------------------------------------- |
| Find a registered format   | [Select a format](Tasks/SelectFormat.md)          |
| Set conversion options     | [Convert a document](Tasks/ConvertDocument.md)    |
| Inspect a neutral document | [Read and write](Tasks/ReadWrite.md)              |
| Extract geometry payloads  | [Extract B-rep](Tasks/ExtractGeometry.md)         |
| Diagnose an exception      | [Error recovery](Tasks/Troubleshoot.md)           |
| Report incorrect guidance  | [Documentation feedback](Maintenance/Feedback.md) |

## Important distinctions

`strict=True` controls reader validation.
`allow_carrier=False` controls registry output policy.
These options are independent.
SOLIDWORKS-to-CATIA conversion can preserve data in a carrier without producing an editable native CATIA part.
Verify native output requirements in the target application.
The default `allow_carrier=True` does not establish native target editability.

Tests run only in remote CI.
Vendor applications are isolated validation oracles and are not production dependencies.
See [repository instructions](../AGENTS.md) and [known gotchas](Gotchas/README.md).
