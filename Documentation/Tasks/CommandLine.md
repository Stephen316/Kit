# Use the Kit command line

## Purpose

Convert CAD files without writing Python.
Inspect decoded records when developing an adapter or researching a format.

## Before you start

Install `uv` and Python 3.11 or later.
Use a Kit revision that contains the command-line interface.
A release published before this change does not contain the `kit` executable.
Preserve the original CAD file and select an unused destination.

From a source checkout, install the command as an isolated tool:

```sh
uv tool install .
```

For a published release containing this interface, use `uv tool install unicad-kit`.
For repository development, follow [repository installation](Install.md), then use `uv run --frozen kit`.
The equivalent module command is `uv run --frozen python -m convert`.
All commands below assume the installed tool is on `PATH`.

## Convert a file

Supply a real source named `part.SLDPRT` before running this example.
The destination `part.json` must be unused.

```sh
kit formats
kit convert part.SLDPRT part.json
```

The source reader is selected from the content and filename.
The destination suffix selects the writer.
For explicit format selection, use the registered identifiers or aliases:

```sh
kit convert part.SLDPRT part.json --from solidworks.sldprt --to interchange.json --json
```

`kit formats --json` lists format identifiers, aliases, suffixes, and independent read/write availability.
For example, SOLIDWORKS is registered for reading only.
Format registration does not establish complete feature coverage.

Expected result: the output file and a conversion report, or a nonzero exit with an error.
The report includes usability claims, transfers, dropped capabilities, external requirements, and writer diagnostics.
The command always uses strict reading and `allow_carrier=False`.
It does not expose an option to bypass the output policy.
An unsuccessful policy check preserves an existing destination through the SDK staging boundary.

A successful command reports writer evidence.
It does not independently verify target-application opening, editing, or rebuilding.
Use [result evaluation](InspectResult.md) for acceptance requirements.

CAUTION: `--overwrite` permits replacement of existing output files, including companion files managed by an adapter.

```sh
kit convert part.SLDPRT part.json --overwrite
```

Use `--configuration NAME` to select a named configuration.
Run `kit convert --help` for the complete option list.

## Decode a file for development

Supply the same real source before these examples.
The neutral view works with registered readers and emits the SDK document JSON.

```sh
kit decode part.SLDPRT -o decoded.json
```

Without `-o`, the command prints JSON to standard output.
A saved decode file is written atomically and protected from replacement by default.
The command rejects the source itself, symlink aliases, and existing hardlink aliases as destinations.

Use the container view to inspect SOLIDWORKS or Fusion archive records:

```sh
kit decode part.SLDPRT --layer container
kit decode part.SLDPRT --layer container --stream Header2 -o header.json
```

The inventory includes names, offsets, sizes, and CRC values.
Fusion records also include the ZIP compression method and directory flag.
`--stream` adds the exact named payload as base64 within the JSON report.
It accepts at most 16 MiB of decoded stream data.
The command does not extract archive-controlled filenames onto the filesystem.

For a real `design.f3d` file, inspect the typed native model:

```sh
kit decode design.f3d --layer native -o native.json
```

This view calls the production Fusion document codec and static state encoder.
It includes the supported typed entity, reference, geometry, history, and material records.
Unknown or unsupported native layouts fail explicitly.
Native structural decoding has a different coverage boundary from neutral conversion and editable output.
The native-state report is a development artifact, not an interchange document for `kit convert`.

Use `--partial` only with the neutral view for research:

```sh
kit decode design.f3d --partial -o partial.json
```

This option selects `strict=False` in the reader.
Inspect the returned diagnostics and opaque payloads before interpreting the result.
A partial decode does not establish conversion support or target editability.
`--configuration` is available only for the neutral view.
`--stream` is available only for the container view.

## Limits and recovery

| Condition                                                       | Behavior and action                                                     |
| --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| CLI input exceeds 256 MiB                                       | Use the Python SDK with an appropriate resource policy                  |
| Argument exceeds 4096 characters or contains control characters | Supply a shorter printable argument                                     |
| Source is missing or not a regular file                         | Supply an existing file                                                 |
| Destination already exists                                      | Select another path, or preserve a copy before using `--overwrite`      |
| Format or feature is unsupported                                | Read the format reference and retain the source for implementation work |
| Container inspection succeeds                                   | Do not infer member decoding, feature coverage, or native acceptance    |
| ZIP method 93 cannot be decoded                                 | Use Python 3.14 for its standard-library Zstandard support              |

The CLI adds no CAD application, debugger, or research runtime dependency.
It exposes existing codecs and does not implement unresolved format semantics.
Only Fusion and SOLIDWORKS currently have container views.
Only Fusion currently has the typed native view.
Source suffixes select those developer views; use `--from` when a filename has another suffix.

Exit status `0` indicates command completion, `1` indicates an operational failure, and `2` indicates invalid usage.
An interrupted command returns `130`.
Operational errors are JSON records on standard error.
Argument errors use the parser's usage message.
`--json` conversion reports contain no progress text on standard output.
Run `kit --help` or `kit --version` for discovery.

Tests execute only in remote CI.
See the [change record](../Changes/Commands/CommandLineInterface.md) for verification evidence and limits.

## Related information

- [Python API](../GettingStarted.md)
- [Format selection](SelectFormat.md)
- [Research tools](../Reference/Research/Tooling.md)
- [Fusion archive inspection](../Gotchas/Conversion/Fusion/FusionArchiveInspection.md)
- [Entry-point specification](https://packaging.python.org/en/latest/specifications/entry-points/)
- [Argument parsing](https://docs.python.org/3.11/library/argparse.html)
