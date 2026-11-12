<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Public API reference

## Purpose and import

Import the supported conversion functions from `convert`.
The distribution name is `unicad-kit`.
Public compatibility names remain lowercase.
Do not replace them with internal PascalCase function names in external callers.

## Entry points

| Callable                                           | Result                 | Purpose                                  |
| -------------------------------------------------- | ---------------------- | ---------------------------------------- |
| `available_adapters()`                             | Tuple of `AdapterInfo` | Read the installed adapter catalogue     |
| `open_document(source, **options)`                 | `CadDocument`          | Read a source without writing            |
| `write_document(document, destination, **options)` | `WriteResult`          | Write a neutral document                 |
| `convert(source, destination, **options)`          | `ConversionResult`     | Read and write through selected adapters |
| `extract_brep(source, directory, **options)`       | Tuple of paths         | Copy available B-rep payloads            |

The public package also exports `ApplicationUsabilityError`, `CarrierReason`, and `registry`.
See [package exports](../../../src/convert/__init__.py).

## Input and destination types

Sources accept paths, bytes, bytearrays, and compatible readable streams.
Destinations accept paths and compatible writable streams.
`extract_brep` additionally accepts an existing `CadDocument`.
Its destination is a directory path.

Use explicit format identifiers for streams without a usable filename.
Match text or binary stream behavior to the selected adapter.
The [type contract](../../../src/convert/adapters/base/ContractTypes.py) defines the accepted interfaces.

## Conversion options

| Keyword                | Default | Meaning                                           |
| ---------------------- | ------- | ------------------------------------------------- |
| `source_format`        | `None`  | Explicit reader identifier                        |
| `destination_format`   | `None`  | Explicit writer identifier                        |
| `configuration`        | `None`  | Configuration passed to reader and writer options |
| `include_brep`         | `True`  | Request B-rep information from the reader         |
| `include_tessellation` | `True`  | Request mesh information from the reader          |
| `strict`               | `True`  | Reader validation policy                          |
| `overwrite`            | `False` | Permit replacement of existing output             |
| `allow_carrier`        | `True`  | Permit carriers subject to registry policy        |
| `write_values`         | `None`  | Adapter-specific writer values                    |

These keyword defaults describe `convert`.
Reader strictness and writer usability policy are independent.
The public API translates `allow_carrier` into writer values.
`WriteOptions` does not have an `allow_carrier` constructor field.

## Options by operation

| Operation            | Accepted keyword options                                                                  |
| -------------------- | ----------------------------------------------------------------------------------------- |
| `open_document`      | `source_format`, `configuration`, `include_brep`, `include_tessellation`, `strict`        |
| `write_document`     | `destination_format`, `configuration`, `overwrite`, `validate`, `allow_carrier`, `values` |
| `extract_brep`       | `source_format`, `overwrite`                                                              |
| `available_adapters` | None                                                                                      |

Shared options retain the defaults in the conversion table.
`write_document` uses `validate=True` and `values=None`.
Its mapping keyword is `values`, not `write_values`.
`convert` always constructs writer options with validation enabled.

## Results

`ConversionResult` contains `document`, `output`, `source_format`, and `destination_format`.
It exposes the writer's transfers, losses, requirements, and usability predicates through properties.
`WriteResult` describes the write directly.
A stream destination normally has no output path.

Read [result evaluation](../../Tasks/InspectResult.md) before interpreting the attestation.
The JSON adapter's usability flags apply to interchange JSON.
They do not claim native CAD application support for JSON.

## Errors and effects

| Failure                         | Public behavior                                   |
| ------------------------------- | ------------------------------------------------- |
| Existing destination            | `FileExistsError` unless replacement is permitted |
| Missing or ambiguous adapter    | Registry selection error                          |
| Invalid input or model          | Reader or model validation error                  |
| Dropped capability              | Capability-loss error                             |
| Unacceptable output attestation | `ApplicationUsabilityError`                       |
| Incorrect returned stream count | `OSError` with partial stream effects possible    |
| Later B-rep extraction failure  | Earlier payload files can remain                  |

Path writes use staging and attempt rollback.
Some backup failures can lose existing targets despite exception handling.
Keep independent backups before replacing files.
If a stream's `write()` returns `None`, the final count check does not run.
Verify output independently when the stream cannot report an accurate count.
Stream writes and payload extraction have different failure boundaries.
See [engine behavior](../Architecture/Engine.md) and [error recovery](../../Tasks/Troubleshoot.md).

## Adapter author contracts

Adapters implement the [reader and writer protocols](../../../src/convert/adapters/base/AdapterProtocols.py).
`ProbeResult` identifies a format, confidence, and reason.
`ReadOptions` and `WriteOptions` are separate records.
Writer results must account for source capabilities and report usable output truthfully.

## Task examples

- [Convert a document](../../Tasks/ConvertDocument.md)
- [Read and write a neutral document](../../Tasks/ReadWrite.md)
- [Extract B-rep payloads](../../Tasks/ExtractGeometry.md)
- [Inspect registered formats](../../Tasks/SelectFormat.md)

## Owning sources

- [Exact public signatures](../../../src/convert/api/__init__.py)
- [Read options](../../../src/convert/adapters/base/ReadOptions.py)
- [Write options](../../../src/convert/adapters/base/WriteOptions.py)
- [Conversion result](../../../src/convert/engine/EngineResult.py)
- [Writer result](../../../src/convert/adapters/base/WriteResult.py)
