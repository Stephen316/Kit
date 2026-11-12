<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# JSON adapter and registry

## Purpose

The JSON adapter stores a neutral `CadDocument` as interchange data.
The registry selects readers and writers for all registered formats.
This reference distinguishes interchange storage from native CAD output.

## JSON identity

| Item              | Value                                |
| ----------------- | ------------------------------------ |
| Format identifier | `interchange.json`                   |
| Suffix            | `.json`                              |
| Media type        | `application/vnd.parashell.kit+json` |
| Main model        | `CadDocument`                        |
| Text encoding     | UTF-8                                |

The probe examines a prefix for the `$type` and `CadDocument` markers.
A `.json` suffix alone is weaker evidence than the document markers.
The reader still needs to decode and validate the complete input.

## Writing

The writer validates the document when `validate=True`.
It serializes the document through the model's JSON interface.
File output ends with a newline.
The JSON codec sorts mapping keys for deterministic text generation.

The writer reports usability for the interchange format.
Those flags do not mean that SOLIDWORKS, FreeCAD, or CATIA can open the JSON as a native model.
Use [read and write](../../Tasks/ReadWrite.md) for an example.

## Payloads

Serialized payloads can contain source information beyond visible geometry.
Inspect the document before sharing its JSON outside the permitted audience.
A neutral document can include private design data or retained native bytes.
JSON readability does not make the content non-sensitive.

## Registry operations

| Operation        | Responsibility                                    |
| ---------------- | ------------------------------------------------- |
| Discovery        | Construct and validate adapter metadata           |
| Reader selection | Resolve an explicit format or probe source data   |
| Writer selection | Resolve an explicit format or destination support |
| Read             | Produce a neutral document                        |
| Write            | Stage output and apply result policy              |

`available_adapters()` returns a deterministic catalogue of adapter metadata.
The catalogue combines registered reader and writer information by format identifier.
It does not independently prove the availability of every operation for every input.

## Streams

Use `destination_format="interchange.json"` for an output stream.
The JSON writer supports compatible text and binary streams.
The registry stages data before its final write to the caller's stream.
A short final write can leave partial output.
See [stream boundaries](../Architecture/Engine.md#stream-destinations).

## Recovery

For invalid JSON or an invalid document type, obtain a valid interchange document.
For ambiguous format selection, supply the explicit format identifier.
For a model validation failure, correct its references before writing.
Do not remove validation merely to make a malformed document serialize.

## Sources

- [Metadata and probe](../../../src/convert/adapters/json/Metadata.py)
- [Reader](../../../src/convert/adapters/json/Reader.py)
- [Writer](../../../src/convert/adapters/json/Writer.py)
- [JSON codec](../../../src/interchange/serialization/JsonCodec.py)
- [Registry discovery](../../../src/convert/adapters/registry/RegistryDiscover.py)
