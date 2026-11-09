<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [README.md](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/README.md)
- [re/Methodology.md](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/re/Methodology.md)
- [tests/convert/api/ApiMetadataTests.py](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/tests/convert/api/ApiMetadataTests.py)
- [AGENTS.md](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/AGENTS.md)
- [src/convert/adapters/solidworks/core/Adapter.py](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/src/convert/adapters/solidworks/core/Adapter.py)

</details>

# Introduction to Kit SDK

Kit is an open-source CAD interchange SDK. It translates geometry, feature trees, assemblies, and other metadata between proprietary CAD formats natively. Kit performs these translations without requiring the original CAD software to be installed on the system.

## Core Architecture

Kit follows a linear pipeline for every file conversion. The system reads a source file through a reader adapter, processes it via an internal model, and writes it using a writer adapter.

```mermaid
flowchart TD
    Source[Source File] --> Reader[Reader Adapter]
    Reader --> Model[Internal CadDocument]
    Model --> Writer[Writer Adapter]
    Writer --> Dest[Destination File]
```

The diagram shows the data flow from a proprietary source format to a destination format through Kit's internal adapters.

### Internal Modeling

Kit uses the `CadDocument` class as its central interchange model. During conversion, the reader adapter builds a `CadDocument` from the source bytes. This document contains:

- **Source Metadata**: Format ID, path, and SHA256 hashes.
- **Geometry**: B-rep models, meshes, and sketch entities.
- **Parametric History**: Features, parameters, and selection sets.
- **Assembly Data**: Definitions, instances, and mates.

## Format Support

Kit provides native support for reading and writing specific proprietary suffixes.

| CAD Software | Extensions Supported      |
| :----------- | :------------------------ |
| SOLIDWORKS   | `.SLDPRT`, `.SLDASM`      |
| FreeCAD      | `.FCStd`                  |
| CATIA        | `.CATPart`, `.CATProduct` |

## Conversion Workflow

You perform conversions using the `convert` function. This function identifies the destination format by the file extension.

See [Getting started](../../GettingStarted.md) for installation and an executable example using the `convert` package.

The operation returns a `ConversionResult`. This object includes the document model, the write result, and an attestation. The attestation details which capabilities (e.g., geometry, parameters) survived the translation.

### Strict Mode

Kit defaults to reversible swaps. You can enable strict mode by passing `allow_carrier=False`. In this mode, the conversion fails with an `ApplicationUsabilityError` if the output is not fully loadable by the vendor application or if data was dropped during the process.

## Development Methodology

Kit relies on a rigorous reverse-engineering playbook to handle proprietary binary formats. The development process follows six distinct phases.

| Phase | Action               | Purpose                                                          |
| :---- | :------------------- | :--------------------------------------------------------------- |
| 1     | Container Framing    | Enumerate streams and crack the file envelope (e.g., ZIP, CFBF). |
| 2     | Measurement Oracle   | Build a way to verify file correctness using the vendor API.     |
| 3     | Differential Corpus  | Create files with single-property variances to locate fields.    |
| 4     | Runtime Tracing      | Use debuggers to find object boundaries and index arithmetic.    |
| 5     | Static Decompilation | Determine field types, version gates, and enum branches.         |
| 6     | Write Path           | Implement the final native writer.                               |

### Verification Discipline

Kit enforces a "no-donor-block" policy. Implementations must avoid shipping vendor bytes and instead emit files from first principles. Developers use a "measurement oracle"—a script that drives the actual CAD software—to confirm that Kit's output matches vendor-produced geometry within the explicitly defined tolerance for each acceptance case.
