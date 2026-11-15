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

For Fusion container stream extraction or native inspection, install with `uv tool install --python 3.14 .`.
These views require Python 3.14; container inventory remains available on older supported interpreters.

For a published release containing this interface, use `uv tool install unicad-kit`.
For repository development, follow [repository installation](Install.md), then use `uv run --frozen kit`.
The full CLI module command is `uv run --frozen python -m KitCli`.
`uv run --frozen python -m convert` supports SDK formats, decoding, and conversion.
Research execution uses `kit research` or `python -m KitCli research` so process access stays outside the SDK runtime.
All commands below assume the installed tool is on `PATH`.

## Convert a file

Supply a real source named `model.f3d` with features supported by the SDK before running this example.
The destination `model.json` must be unused.

```sh
kit formats
kit convert model.f3d model.json
```

The source reader is selected from the content and filename.
The destination suffix selects the writer.
Unknown or ambiguous suffixes require `--to FORMAT`; the CLI does not fall back to another output type.
An explicit format still retains the selected writer's filename constraints; JSON output requires a `.json` pathname.
For explicit format selection, use the registered identifiers or aliases:

```sh
kit convert model.f3d model.json --from fusion.f3d --to interchange.json --json
```

`kit formats --json` lists format identifiers, aliases, suffixes, and independent read/write availability.
For example, SOLIDWORKS is registered for reading only.
Format registration does not establish complete feature coverage.

Expected result: the output file and a conversion report, or a nonzero exit with an error.
The report includes usability claims, transfers, dropped capabilities, external requirements, and writer diagnostics.
The command always uses strict reading and `allow_carrier=False`.
It also requires every capability transfer to be native; mixed transfers and intrinsic target-limitation carriers are refused before output publication.
It refuses native-only feature definitions or sketch geometry before writing, including in nested components.
Component, mate, mate-entity, sketch-entity and sketch-constraint kinds must be known nonnative values.
Native enum values, `"native"` strings and unknown kind strings are refused even when their links or geometry objects are valid.
Retained native payloads, opaque B-rep records, and explicit incomplete assembly references or transforms are also refused.
Nonempty FreeCAD `external_documents` metadata is refused because its sidecars bypass parent qualification; see [metadata sidecars](../Changes/Commands/ExternalDocumentGuard.md).
Nonempty FreeCAD `objects` metadata is also refused because text-only properties can replay a captured graph; see [captured objects](../Changes/Commands/CapturedObjectGuard.md).
Assemblies with placed instances remain inspection-only because their placement history has no qualified SDK contract; see [assembly placement](../Changes/Commands/AssemblyPlacementGuard.md).
Retained source keys and binary metadata values are refused through nested containers and embedded documents; ordinary provenance text and digests remain eligible.
Local B-rep, meshes, or bodies without a feature timeline are refused, including nested documents and local assembly geometry.
Every document requires model feature history; parameter-only and empty assembly documents remain inspection-only.
An entirely inactive timeline cannot supply that history, and standalone support planes require SDK geometry qualification; see [active history](../Changes/Commands/ActiveModelHistory.md).
Each sketch requires a reference feature, including nested sketches; see [sketch history](../Changes/Commands/SketchHistoryGuard.md).
Every sketch requires active driving dimensions, including solid profiles, and a matching SDK regeneration contract; see [model qualification](../Changes/Commands/ParametricModelGuard.md).
Definitionless operations and native, imported, or unknown feature kinds are refused; a supported sketch reference cannot substitute for a typed generator of local geometry.
Each B-rep body must link to a local design body with a typed generating final feature.
Final generators and their transitive feature dependencies must remain active; suppression in any configuration is refused conservatively for those body histories.
Creation requires validated controls and an active declared profile reference; modifiers require generated inputs, and boolean combine requires two distinct generated operands.
Creator contours currently support one finite positive-radius circle or a simple closed three/four-sided straight ring; member tags must match geometry, and more complex profiles remain inspection-only.
Body and B-rep conversion also requires Python 3.14 and a matching SDK Fusion authoring/native-state regeneration contract; generic typed histories remain inspection-only.
Meshes are refused because their model has no typed ownership link to a generator; provenance and free-form ownership tags do not establish one.
Use `kit decode` or the pinned research readers to inspect those unsupported semantics.
It does not expose an option to bypass the output policy.
An unsuccessful policy check preserves an existing destination through the SDK staging boundary.

A successful command reports writer evidence.
It does not independently verify target-application opening, editing, or rebuilding.
Use [result evaluation](InspectResult.md) for acceptance requirements.

CAUTION: `--overwrite` permits replacement of existing output files, including companion files managed by an adapter.

```sh
kit convert model.f3d model.json --overwrite
```

Use `--configuration NAME` to select a named configuration.
Run `kit convert --help` for the complete option list.

## Decode a file for development

Supply a real source named `part.SLDPRT` before these examples.
The neutral view works with registered readers and emits a development report.
Its `document` field contains the SDK document JSON.
The report records `kind: "kit.decode"`, `layer`, and the explicit `partial` selection.
It is not an interchange document accepted by `kit convert`.

```sh
kit decode part.SLDPRT -o decoded.json
```

Without `-o`, the command prints JSON to standard output.
A saved decode file is written atomically and protected from replacement by default.
New files respect the process umask; replacement preserves existing permission bits.
Home-relative source and destination paths are expanded before alias validation.
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
SOLIDWORKS container inspection limits total decoded streams to 128 MiB before each inflation.
Other read paths retain their existing SDK resource limits.
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

## Deterministic research

Use [the research CLI](ResearchCommandLine.md) for PR #94 pinned readers and existing controller/supervisor commands.
Working-file inspection reports remain distinct from committed-input documents, receipts, and run summaries.

## Limits and recovery

| Condition                                                       | Behavior and action                                                     |
| --------------------------------------------------------------- | ----------------------------------------------------------------------- |
| CLI input exceeds 256 MiB                                       | Use the Python SDK with an appropriate resource policy                  |
| Argument exceeds 4096 characters or contains control characters | Supply a shorter printable argument                                     |
| Source is missing or not a regular file                         | Supply an existing file                                                 |
| Destination already exists                                      | Select another path, or preserve a copy before using `--overwrite`      |
| Format or feature is unsupported                                | Read the format reference and retain the source for implementation work |
| Container inspection succeeds                                   | Do not infer member decoding, feature coverage, or native acceptance    |
| Fusion stream extraction or native inspection requires 3.14     | Install with `uv tool install --python 3.14 .`                          |

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
`--version` is a top-level option; place it before a subcommand.

Tests execute only in remote CI.
See the [change record](../Changes/Commands/CommandLineInterface.md) for verification evidence and limits.

## Related information

- [Python API](../GettingStarted.md)
- [Format selection](SelectFormat.md)
- [Research tools](../Reference/Research/Tooling.md)
- [Fusion archive inspection](../Gotchas/Conversion/Fusion/FusionArchiveInspection.md)
- [Entry-point specification](https://packaging.python.org/en/latest/specifications/entry-points/)
- [Argument parsing](https://docs.python.org/3.11/library/argparse.html)
