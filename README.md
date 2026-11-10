<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

<p align="center">
  <img alt="banner" src="https://github.com/TryParashell/Kit/blob/e93626c79ab6667753f9fccfe4d7c5245cbc457b/files/Banner.png">
</p>

# Kit

Kit by Parashell is an open-source CAD interchange SDK for translating geometry, feature trees, assemblies and more between proprietary formats.

## Documentation

Read the [documentation index](Documentation/Index.md), [getting-started guide](Documentation/GettingStarted.md),
and [GitHub wiki](https://github.com/TryUniCAD/Kit/wiki). Contributors must add
[documentation entries](Documentation/Changes/Index.md) for new additions and record
new discoveries in the [gotchas log](Documentation/Gotchas/README.md).

## _Currently_ supported CAD software

- SOLIDWORKS
- Parashell
- FreeCAD

## _Planned_ (in-order)

1. Fusion (full translation)
2. CATIA
3. NX
4. Rhino
5. Creo
6. AutoCAD

## Supported formats

| CAD        | Suffixes                  | Registered adapters |
| ---------- | ------------------------- | ------------------- |
| SOLIDWORKS | `.SLDPRT`, `.SLDASM`      | Reader and writer   |
| FreeCAD    | `.FCStd`                  | Reader and writer   |
| CATIA      | `.CATPart`, `.CATProduct` | Reader and writer   |

Kit adapters run without requiring CAD software. The partial Fusion reader is
available for [format research](re/Fusion/README.md#research-reader).

## Architecture

Every conversion follows one route:

```text
source file -> reader adapter -> (ORACLE) -> writer adapter -> destination file
```

## Converting

`convert(source, destination)` reads the source, builds a `CadDocument`, and writes the destination format inferred from its suffix:

```python
from convert import convert

result = convert("bracket.SLDPRT", "bracket.FCStd")
```

The returned `ConversionResult` carries the document, the write result, and the attestation describing which capabilities survived the round trip.

### Default reversible swaps

By default a conversion is reversible.

### Strict mode

Pass `allow_carrier=False` to refuse a carrier result. The write then fails with
`ApplicationUsabilityError` unless the attestation reports the output as application usable and
vendor loadable, with nothing dropped and no unmet requirements:

```python
result = convert("bracket.SLDPRT", "bracket.FCStd", allow_carrier=False)
```

## Distribution

Kit is licensed under the [MIT License](LICENSE).

Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt.

Third-party materials retain their respective licenses; see [the vendor binary notice](re/binaries/README.md).
