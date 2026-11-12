<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Convert a document

## Purpose

Read one CAD document and request an output from another adapter.
This procedure applies to Python callers of `convert`.
It includes the output checks needed before acceptance.

## Before you start

- Complete the [installation procedure](Install.md).
- Select formats with the [adapter catalogue](SelectFormat.md).
- Keep a separate copy of the original source.
- Select an unused destination path.
- Identify the configuration and required capabilities.

The paths `bracket.SLDPRT` and `bracket.FCStd` are example paths.
Supply a real input at the source path before executing the example.
A file with unsupported content can fail even when its suffix has an adapter.

## Procedure

1. Request a conversion with output policy enabled.

   ```python
   from convert import convert as ConvertDoc

   Result = ConvertDoc(
       "bracket.SLDPRT",
       "bracket.FCStd",
       allow_carrier=False,
   )
   ```

2. Record `Result.source_format` and `Result.destination_format`.
3. Inspect `Result.output` with the [result procedure](InspectResult.md).
4. Record all capability transfers.
5. Check the required vendor acceptance evidence.

Expected result: the API returns a `ConversionResult`, or it raises an error.
A returned result is writer evidence.
It is not an independent measurement from the target application.

## Select options

| Need                    | Option                | Effect                                               |
| ----------------------- | --------------------- | ---------------------------------------------------- |
| Explicit reader         | `source_format`       | Selects the input adapter                            |
| Explicit writer         | `destination_format`  | Selects the output adapter                           |
| Named configuration     | `configuration`       | Passes the selection to reader and writer options    |
| Reader validation       | `strict=True`         | Applies the reader's strict policy                   |
| Output usability policy | `allow_carrier=False` | Rejects results that fail the registry output policy |
| Adapter-specific values | `write_values`        | Passes values to the writer                          |

Keep `include_brep=True` and `include_tessellation=True` for lossless conversion.
Read filters can change the information available to the writer.
Do not claim preservation of information that you excluded during reading.

## Replace an existing destination

CAUTION: `overwrite=True` permits replacement of existing output files.
Preserve any required copy before you enable this option.

Use a new destination path when replacement is unnecessary.
The registry stages path output before it checks the write result.
Companion files can also form part of an output bundle.
See [write boundaries](../Reference/Architecture/Engine.md).

## If the task fails

For `ApplicationUsabilityError`, record the structured error with the [recovery procedure](Troubleshoot.md).
Do not set `allow_carrier=True` to bypass an acceptance failure.
Carrier output is not an accepted translation.
The runtime can return carrier output, but that return does not satisfy the product acceptance gate.
Keep incomplete output as diagnostic evidence and continue the implementation work.

For a filesystem error, check destination permissions, free space, and existing companion paths.
For unsupported source content, preserve the source and report its format and feature family.
Stop before distributing an output that has no required acceptance evidence.

## Sources

- [Public conversion signature](../../src/convert/api/__init__.py)
- [Conversion option construction](../../src/convert/api/ApiConvert.py)
- [Output policy](../../src/convert/adapters/base/WritePolicy.py)
