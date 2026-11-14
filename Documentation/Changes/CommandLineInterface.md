# Conversion and developer decoding CLI

## Behavior

Kit now installs the `kit` executable alongside its Python SDK.
`python -m convert` uses the same parser and command implementation.
The existing `kit` plugin entry-point group remains compatible.
The CLI uses standard-library argument parsing and introduces no runtime dependency.

## Plan and implementation

1. Expose registered reader and writer discovery through `kit formats`.
2. Connect `kit convert SOURCE DESTINATION` to the existing conversion engine.
3. Apply strict reading and the registry output policy on every conversion.
4. Expose neutral, container, and typed native decoding through `kit decode`.
5. Protect source files and stage developer JSON output before publication.
6. Verify installed commands and actual file boundaries in remote CI.

The conversion report distinguishes writer evidence from target-application acceptance.
It includes transfer representations, usability claims, dropped capabilities, external requirements, and diagnostics.
Existing SDK defaults and adapter qualification boundaries remain unchanged.

The neutral decode view emits `CadDocument` JSON from any registered reader.
Its explicit `--partial` switch selects the reader's research mode.
Container decoding inventories SOLIDWORKS and Fusion members and can expose one payload as base64.
Fusion native decoding emits the production typed document model through the static state encoder.
These development views do not establish editable conversion coverage.

## Usage and limits

Follow [the command-line procedure](../Tasks/CommandLine.md) for installation, examples, recovery, and exit statuses.
Use `kit formats`, `kit convert input.SLDPRT output.json`, or `kit decode input.f3d --layer native`.
`--json` selects machine-readable conversion and discovery reports.
`-o` selects a decode output file; otherwise decoding writes JSON to standard output.

Conversions do not expose partial reading or an output-policy bypass.
Outputs require explicit `--overwrite` to replace existing files.
The CLI rejects source/output path identity, including existing hardlink and symlink aliases.
Decode output uses a temporary sibling and atomic publication without following archive member paths.
Inputs are limited to 256 MiB, individual stream exports to 16 MiB, and arguments to 4096 printable characters.
Use the SDK when larger input files require a separately managed resource policy.

The CLI does not implement missing reverse-engineering semantics.
It does not launch CAD applications or include the research workspace in the wheel.
Fusion method 93 decoding requires a compatible standard-library codec, available in Python 3.14.
Container inventory alone does not verify member CRCs or feature semantics.

## Verification

Source inspection verified public option mapping, format discovery, static native-state encoding, and output staging.
Pinned Black, Pyright, and Mypy checks cover the new source and process coverage.
No local tests or command smoke tests were run, as required by repository policy.

New remote process cases cover the installed console command, module execution, adapter discovery, SOLIDWORKS-to-JSON conversion, and Fusion/JSON native round trips.
They also cover container inventory and stream bytes, native records, partial reading, invalid arguments, malformed files, source aliases, existing outputs, and input limits.
Wheel metadata checks verify both console and SDK plugin entry points.
The existing Fusion compatibility job runs the new process cases; complete acceptance remains deferred to the merge-group candidate.
Remote execution results and current-head review evidence are recorded in the PR.
No new vendor-application acceptance is claimed by this CLI change.
