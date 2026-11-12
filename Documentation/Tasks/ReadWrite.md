<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Read and write a neutral document

## Purpose

Separate the read operation from the write operation.
Use this procedure when your application must inspect the neutral document before writing.

## Before you start

- Complete the [installation procedure](Install.md).
- Supply a real source file at `bracket.SLDPRT`.
- Select an unused destination named `bracket.json`.
- Identify the document information required by the task.

JSON output is Kit interchange data.
It is not a native CAD application document.

## Procedure

1. Read the source into a neutral document.

   ```python
   from convert import open_document as OpenDoc

   DocumentData = OpenDoc("bracket.SLDPRT")
   ```

2. Inspect the [document model](../Reference/Model/Document.md).
3. Write the document to the selected interchange format.

   ```python
   from convert import write_document as WriteDoc

   WriteResult = WriteDoc(
       DocumentData,
       "bracket.json",
       destination_format="interchange.json",
       allow_carrier=False,
   )
   ```

4. Evaluate the returned `WriteResult`.

Expected result: the writer returns its output record.
The example preserves the separation between the source model and the output attestation.

## Options

`open_document` accepts reader options.
It does not accept `overwrite` or `allow_carrier`.
`write_document` accepts writer options.
Its adapter-specific mapping is named `values`, not `write_values`.

Keep `validate=True` when you write an inspected or modified document.
Model validation checks structural contracts.
It does not execute the vendor application or solve every modeling operation.

## Streams

Use an explicit format identifier for a stream without a filename.
The JSON adapter accepts a text destination.
Binary formats require a compatible binary destination.

```python
from io import StringIO as TextStream
from convert import write_document as WriteDoc

OutputStream = TextStream()
WriteResult = WriteDoc(
    DocumentData,
    OutputStream,
    destination_format="interchange.json",
    allow_carrier=False,
)
JsonText = OutputStream.getvalue()
```

The stream write uses temporary storage before the output policy check.
After that check, the final write uses the caller's stream.
A short write can leave that stream partially changed.
The count check requires a returned count from the stream's `write()` method.
A return value of `None` bypasses that check.
Use a reliable count or independently verify the written content.
Do not assume that arbitrary streams support rollback.

## If the task fails

For an ambiguous writer, set `destination_format` explicitly.
For invalid model references, correct the model before writing again.
For a failed destination stream, create a fresh stream before retrying.
See [error recovery](Troubleshoot.md).

## Sources

- [Public signatures](../../src/convert/api/__init__.py)
- [Stream staging](../../src/convert/adapters/staging/StreamStaging.py)
- [JSON writer](../../src/convert/adapters/json/Writer.py)
