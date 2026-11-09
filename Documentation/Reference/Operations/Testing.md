<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [re/Methodology.md](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/re/Methodology.md)
- [tests/convert/formats/SwapsTests.py](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/tests/convert/formats/SwapsTests.py)
- [tests/convert/catia/CatiaTests.py](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/tests/convert/catia/CatiaTests.py)
- [tests/convert/freecad/FreecadTests.py](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/tests/convert/freecad/FreecadTests.py)
- [tests/convert/solidworks/core/SolidworksWriterTests.py](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/tests/convert/solidworks/core/SolidworksWriterTests.py)
- [AGENTS.md](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/AGENTS.md)
- [re/solidworks/archive/Grammar.md](https://github.com/TryUniCAD/Kit/blob/aeff047c355622e812ab5d79b665d8f64c4075bb/re/solidworks/archive/Grammar.md)
</details>

# Translation Testing Strategies

Run tests only in remote CI. PR checks cover static and policy validation; heavy acceptance runs on the merge-group candidate. Unit tests are prohibited. Vendor oracle experiments require an isolated validation environment and are never invoked by production conversion. See [the queue guide](../../../MergeQueue.md).

Translation testing strategies ensure the quantitative correctness and interoperability of CAD format conversions. The project prioritizes lossless, vendor-loadable, and parametric output verified through measurement oracles and extensive cross-format swap matrices.

Testing behavior focuses on integration, end-to-end, and smoke tests at real component boundaries rather than isolated unit tests. Verification procedures utilize vendor APIs only for validation, ensuring that the core converter maintains independence from proprietary runtime dependencies.

## The Measurement Oracle

A measurement oracle provides a quantitative verdict on file correctness by querying a vendor application for geometric scalars. Qualitative verdicts like "file opens" are insufficient for proving translation accuracy.

### Oracle Requirements

- **Quantitative Data**: You must use numbers determined by geometry, such as solid volume in m³ or center of mass.
- **Precision**: Match values to a relative tolerance, typically ≤6e-16 or ≤1e-6 depending on the target.
- **Process Isolation**: Run one fresh vendor process per candidate file to prevent crash poisoning or silent install degradation.
- **Control Batches**: Measure a known-good vendor file at the start and end of every batch. Discard the entire batch if the control fails.

### Automation Surface

Testing automation interfaces with vendor software in a specific preference order to obtain oracle data:

1.  Vendor COM / .NET / Scripting API (e.g., SOLIDWORKS COM, NXOpen, CATIA CAA).
2.  Headless CLI.
3.  UI Automation.

## Differential Corpus Analysis

Differential analysis locates binary fields by comparing families of documents that vary in exactly one property. This method identifies where specific parameters, such as depth or feature count, are stored within a proprietary format.

### Corpus Design

- **Control Pairs**: You author the same document twice to identify "noise" like timestamps and session IDs.
- **Family Ladders**: You create files with incremental changes (e.g., 1, 2, 3... n features) to identify repeating blocks.
- **Boolean Coverage**: You exercise both "on" and "off" states for every boolean flag.
- **Production Corpus**: You collect real-world user data to test localization and handle values not produced by authored files.

```mermaid
flowchart TD
    A[Author Single-Var Family] --> B[Diff Within Family]
    B --> C{Field Found?}
    C -->|Yes| D[Map Parameter Offset]
    C -->|No| E[Increase Variation]
    D --> F[Verify with Oracle]
    F --> G[Confirm Confirmed/Partial Status]
```

The diagram shows the iterative process of identifying data fields using a differential corpus and confirming them via geometric measurement.

## Cross-Format Swap Matrix

The swap matrix verifies that a document can transition through multiple formats and return to its original state without data loss. You test these transitions using a representative set of parts and assemblies from each supported format.

### Supported Testing Formats

| Extension   | Format Identifier |
| :---------- | :---------------- |
| .SLDPRT     | solidworks.sldprt |
| .SLDASM     | solidworks.sldasm |
| .FCStd      | freecad.fcstd     |
| .CATPart    | catia.v5          |
| .CATProduct | catia.v5          |

### Verification Tiers

A successful translation must pass multiple verification checks during a swap:

- **Application Usability**: The file can be modified or extended in the target CAD package.
- **Vendor Loadable**: The vendor application opens the file without errors or rebuild crashes.
- **Semantic Equality**: The restored document signature (configurations, parameters, planes, etc.) matches the original source signature.
- **Near-Lossless Proof**: Record every dropped capability and unmet requirement. Any loss fails the repository's lossless acceptance criterion, even if the target format lacks support.

## Native Replay and Byte Identity

Native replay strategies verify that the converter can handle proprietary binary streams without corruption. You use byte-identity checks to confirm that re-emitted files match their sources exactly when no neutral edits are performed.

### Segmentation and Renumbering

To insert, delete, or reorder objects in proprietary streams (like MFC-style `CArchive`), you must trace object boundaries and recompute map indices.

```mermaid
sequenceDiagram
    participant Test as Test Suite
    participant Conv as Converter
    participant Trace as Research Tracer
    participant Vendor as Isolated Vendor Reader
    Test->>Trace: Observe research candidate
    Trace->>Vendor: Trace reader entry points
    Vendor-->>Trace: Record object spans and indices
    Trace-->>Test: Store format findings
    Test->>Conv: Read source with recovered grammar
    Conv->>Conv: Reparse to Symbolic Model
    Conv->>Conv: Re-emit with New Indices
    Conv-->>Test: Compare Bytes (Byte-Identity)
```

The diagram represents the verification flow for confirming object segmentation and index renumbering accuracy through byte-identity testing.

### Replay Compatibility Modes

| Mode                            | Description                                                                                                         |
| :------------------------------ | :------------------------------------------------------------------------------------------------------------------ |
| **native-exact**                | A mode label for exact replay; independently compare bytes and semantic results before claiming identity.           |
| **native-base-neutral-overlay** | Native streams are preserved exactly, while neutral edits are carried in a sidecar (e.g., `KitInterchange` stream). |
| **kit-neutral-only**            | No native streams are preserved; the file depends entirely on the neutral manifest.                                 |

## Verification Discipline

The project enforces a strict three-tier confidence system for all discovered fields to prevent silent corruption:

1.  **Confirmed**: The field is decompiled and reproduces a real measured number or traced span.
2.  **Partial**: The field is decompiled but no available corpus file exercises it. Keep these marked as unverified research; do not synthesize values or copy donor spans into production output.
3.  **Not Found**: The field is unresolved.

### Rule of Stale Caches

Formats often contain derived caches (e.g., bounding boxes, Parasolid geometry caches). You must identify which fields are authored parameters and which are derived. Do not assume a stale cache is safe: verify recomputation for the specific field and vendor version. Invalid caches can crash the application or corrupt geometry.
