<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Extract B-rep payloads

## Purpose

Copy available B-rep payloads from a source or neutral document into a directory.
This operation extracts geometry data.
It does not create a complete editable target document.

## Before you start

- Complete the [installation procedure](Install.md).
- Supply a readable source at `bracket.SLDPRT`.
- Select a task-owned output directory.
- Keep the source unchanged.

The source must contain B-rep data that the reader exposes.
Some documents contain feature history without an extractable B-rep payload.

## Procedure

1. Extract the available payloads.

   ```python
   from convert import extract_brep as ExtractBrep

   OutputPaths = ExtractBrep("bracket.SLDPRT", "GeometryOutput")
   ```

2. Record every returned path.
3. Record the payload format and source identity.
4. Check whether the result contains the geometry needed by the task.

Expected result: the function returns a tuple of output paths.
An empty tuple means that the operation wrote no available payloads.
Do not interpret an empty result as a successful geometry translation.

## Existing files

The default `overwrite=False` rejects an existing output path.
CAUTION: `overwrite=True` permits replacement of existing payload files.
Preserve required files before you enable replacement.

This extraction function writes payloads in sequence.
It does not use the conversion registry's staged multi-file output transaction.
An error on a later payload can leave earlier files in the output directory.
Use a separate directory for each extraction attempt.

## Neutral document input

The function also accepts a `CadDocument`.
If that document was read without B-rep data, extraction cannot recover the excluded bytes.
Read the source again with `include_brep=True` when the task requires them.

## If the task fails

| Symptom                 | Action                                                      |
| ----------------------- | ----------------------------------------------------------- |
| Existing file error     | Select a new output directory                               |
| Empty output tuple      | Check the reader result and source geometry                 |
| Error after some writes | Record the partial paths before retrying in a new directory |
| Unsupported payload     | Record the source format and payload metadata               |

Do not treat an extracted geometry file as evidence of preserved feature history.
See [result evaluation](InspectResult.md) for product acceptance.

## Sources

- [Extraction implementation](../../src/convert/api/ApiBrep.py)
- [Payload selection](../../src/convert/geometry/BrepPayloads.py)
- [Payload filenames](../../src/convert/geometry/BrepNames.py)
