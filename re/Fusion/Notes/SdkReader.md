<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Public SDK reader

[Fusion feature index](../README.md)

The adapter catalog includes `fusion.f3d` with alias `f3d`. The registry
detects the active Fusion design streams in a saved archive. Call
`open_document` with `strict=False` to opt into the partial projection.
The public reader validated 766 histories across 712 tracked archives
with Python 3.14.

```python
from convert import open_document

document = open_document("part.f3d", strict=False)
```

For a qualified local assembly, `open_document("assembly.f3d", strict=False)`
returns the graph in `document.assembly`. Pass a decimal configuration string,
for example `configuration="35"`, to read a single history on its own. An archive
with multiple histories that cannot be bound to a supported assembly requires
an explicit history ID. Setting `include_brep=False` omits the projected B-rep and preserves the original
document payload. The adapter supplies a reader for `.f3d`. Native Fusion
output and strict source translation require further format coverage.

For a qualified body collection, `fusion.body_inventory` is available in
`document.metadata` for a selected history, or in each assembly definition's
`attributes`. It reports the native component ID and ordered B-rep members.
A qualified empty collection has an empty `members` tuple. Each member retains
its native object and collection IDs, the stored name, and the Kit
`design_body_id` when a body has already been reconstructed.

For archives with Zstandard-compressed members, the convenience API uses
Python's ZIP Zstandard support. On an earlier Python version, supply a
Zstandard decompression callback through `ReadOptions.values` when reading
with the registry.

```python
from convert.adapters import AdapterRegistry, ReadOptions

def read_fusion_with_codec(path, inflate_zstd):
    registry = AdapterRegistry()
    registry.introspect()
    return registry.read(
        path,
        format_id="fusion.f3d",
        options=ReadOptions(
            strict=False,
            values={"fusion.inflate_zstd": inflate_zstd},
        ),
    )
```

The callback takes compressed bytes and an expected uncompressed size. Kit
checks the result against the archive's size and CRC.
