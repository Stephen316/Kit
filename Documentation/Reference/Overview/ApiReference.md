<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# API reference

The installed public import is `convert`. Its compatibility names are intentionally lowercase; implementation functions live in focused PascalCase modules.

## Public entry points

| Callable                                           | Result                 | Purpose                                                      |
| -------------------------------------------------- | ---------------------- | ------------------------------------------------------------ |
| `convert(source, destination, **options)`          | `ConversionResult`     | Read a source document and write it through a target adapter |
| `open_document(source, **options)`                 | `CadDocument`          | Read a document without writing an output                    |
| `write_document(document, destination, **options)` | `WriteResult`          | Write an existing neutral document                           |
| `extract_brep(source, directory, **options)`       | Tuple of paths         | Extract available B-rep payload files                        |
| `available_adapters()`                             | Tuple of `AdapterInfo` | Discover registered formats                                  |

Sources accept filesystem paths, bytes, bytearrays, or supported readable streams. Destinations accept paths or supported writable streams. Explicit format IDs are useful for streams with no suffix. See [the source and destination contracts](../../../src/convert/adapters/base/ContractTypes.py).

## Conversion options

| Keyword                | Default | Meaning                                                                              |
| ---------------------- | ------- | ------------------------------------------------------------------------------------ |
| `source_format`        | `None`  | Explicit reader format ID                                                            |
| `destination_format`   | `None`  | Explicit writer format ID                                                            |
| `configuration`        | `None`  | Configuration selection                                                              |
| `include_brep`         | `True`  | Request B-rep data during reading                                                    |
| `include_tessellation` | `True`  | Request mesh data during reading                                                     |
| `strict`               | `True`  | Reader validation policy                                                             |
| `overwrite`            | `False` | Permit replacing an existing output                                                  |
| `allow_carrier`        | `True`  | Permit results that preserve data without meeting application-usability requirements |
| `write_values`         | `None`  | Adapter-specific write values                                                        |

`strict` and `allow_carrier` are independent. The API translates carrier policy into write values; `WriteOptions` does not have an `allow_carrier` constructor field. `write_document` uses `values` rather than `write_values` and additionally accepts `validate=True`. `open_document` accepts the reader options only. `extract_brep` accepts `source_format` and `overwrite`.

```python
from convert import convert as ConvertDoc

Result = ConvertDoc("bracket.SLDPRT", "bracket.FCStd", allow_carrier=False)
```

`ConversionResult` exposes `document`, `output`, `source_format`, `destination_format`, `transfers`, `dropped`, `requirements`, `application_usable`, `vendor_loadable`, `roundtrip_safe`, and `near_lossless`. Inspect these individually; carrier retention and byte identity do not prove an editable feature tree.

The exact callable signatures are maintained in [the public API](../../../src/convert/api/__init__.py), [conversion orchestration](../../../src/convert/api/ApiConvert.py), and [result model](../../../src/convert/engine/EngineResult.py). These sources take precedence over prose.

## Adapter contracts

Adapters implement the [reader/writer protocols](../../../src/convert/adapters/base/AdapterProtocols.py). Probing returns a [ProbeResult](../../../src/convert/adapters/base/ProbeResult.py) with `format_id`, `confidence`, and `reason`; compatibility properties include `FormatId`, `Confidence`, and `ReasonText`. Reader and writer options are separate immutable records: [ReadOptions](../../../src/convert/adapters/base/ReadOptions.py) and [WriteOptions](../../../src/convert/adapters/base/WriteOptions.py).

Vendor applications are isolated validation oracles, never a step invoked by the production conversion API. See [acceptance requirements](../../../.agents/skills/standard-pr-practice/references/Standards/Portable/LosslessTranslation.md).
