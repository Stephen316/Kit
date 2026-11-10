<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Fusion research reader

[Fusion feature index](../README.md)

Production adapter discovery excludes the partial Fusion reader. Research
tools can instantiate it directly and select the available history projection.

```python
from convert.adapters.Fusion.Adapter import FusionReader
from convert.adapters.base.ReadOptions import ReadOptions

document = FusionReader().read("part.f3d", ReadOptions(strict=False))
```

For a qualified local assembly, the reader returns the graph in
`document.assembly`. Set `configuration="35"` in `ReadOptions` to select a
single history. An archive with multiple histories that cannot be bound to a
supported assembly requires an explicit history ID. Set `include_brep=False`
to omit the projected B-rep and preserve the original document payload.

For a qualified body collection, `fusion.body_inventory` is available in
`document.metadata` for a selected history, or in each assembly definition's
`attributes`. It reports the native component ID and ordered B-rep members.
A qualified empty collection has an empty `members` tuple. Each member retains
its native object and collection IDs, the stored name, and the Kit
`design_body_id` when a body has already been reconstructed.

For archives with Zstandard-compressed members, the reader uses
Python's ZIP Zstandard support. On an earlier Python version, supply a
Zstandard decompression callback through `ReadOptions.values` when reading
directly with the adapter.

```python
from convert.adapters.Fusion.Adapter import FusionReader
from convert.adapters.base.ReadOptions import ReadOptions

def read_fusion_with_codec(path, inflate_zstd):
    return FusionReader().read(
        path,
        options=ReadOptions(
            strict=False,
            values={"fusion.inflate_zstd": inflate_zstd},
        ),
    )
```

The callback takes compressed bytes and an expected uncompressed size. Kit
checks the result against the archive's size and CRC.
