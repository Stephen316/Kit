<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Select a reader and writer

## Purpose

Identify an adapter before a conversion.
Use explicit format identifiers when a path or stream cannot identify the intended format.

## Before you start

- Complete the [installation procedure](Install.md).
- Identify the source file and intended output format.
- Keep the original file unchanged.

An adapter catalogue describes registration and declared capabilities.
It does not prove vendor acceptance for a particular file.

## Procedure

1. Read the registered adapter metadata in your Python application.

   ```python
   from convert import available_adapters as ListAdapters

   for AdapterData in ListAdapters():
       print(AdapterData.format_id, AdapterData.aliases, AdapterData.extensions)
   ```

2. Match the input to a registered reader format.
3. Match the destination to a registered writer format.
4. Read the format-specific limitations.
5. Record the chosen identifiers with the conversion request.

Expected result: the request identifies the intended source and destination formats.
If more than one writer matches a stream, supply `destination_format` explicitly.

## Registered format identifiers

| Identifier          | File suffix               | Reference                                                 |
| ------------------- | ------------------------- | --------------------------------------------------------- |
| `solidworks.sldprt` | `.SLDPRT`                 | [SOLIDWORKS adapter](../Reference/Adapters/Solidworks.md) |
| `solidworks.sldasm` | `.SLDASM`                 | [SOLIDWORKS adapter](../Reference/Adapters/Solidworks.md) |
| `freecad.fcstd`     | `.FCStd`                  | [FreeCAD adapter](../Reference/Adapters/Freecad.md)       |
| `catia.v5`          | `.CATPart`, `.CATProduct` | [CATIA adapter](../Reference/Adapters/Catia.md)           |
| `interchange.json`  | `.json`                   | [JSON adapter](../Reference/Adapters/Json.md)             |

The discovery result from the installed revision takes precedence over this table.
Each catalogue entry has one primary `format_id` and can have additional `aliases`.
The SOLIDWORKS entry uses `solidworks.sldprt` as its primary identifier.
Its `aliases` field contains `solidworks.sldasm` for assemblies.
Discovery does not return a separate entry for that alias.
Fusion research code does not register `fusion.f3d` in the production catalogue.
See the [Fusion research entry](../Changes/FusionResearchImport.md).

## Selection behavior

The registry can probe input content.
A filename suffix helps selection but does not validate the complete file.
For output paths, the suffix normally identifies the writer.
For output streams, an explicit identifier avoids ambiguous writer selection.

Do not rename a file to imply another format.
Do not treat a probe confidence value as a lossless-conversion result.
Use [result evaluation](InspectResult.md) after the write.

## If the task fails

| Symptom                                 | Action                                                   |
| --------------------------------------- | -------------------------------------------------------- |
| No reader matches                       | Confirm the source type and registered format identifier |
| More than one writer matches            | Set the explicit destination identifier                  |
| The suffix conflicts with content       | Obtain the correct source file                           |
| The format is research-only             | Use the documented research workflow outside production  |
| An adapter exists but rejects a feature | Record the feature and structured error                  |

Stop if the intended format has no registered production adapter.
Do not add a vendor-runtime fallback to the conversion path.

## Sources

- [Public discovery](../../src/convert/api/ApiAvailable.py)
- [Writer selection](../../src/convert/adapters/registry/RegistrySelect.py)
- [Adapter discovery](../../src/convert/adapters/registry/AdapterDiscovery.py)
