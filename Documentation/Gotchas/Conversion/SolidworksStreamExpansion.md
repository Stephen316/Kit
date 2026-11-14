# Source size does not bound SOLIDWORKS stream expansion

A small compressed file can contain streams whose declared decoded size is much larger.
Checking input-file size or an export limit after container parsing does not bound that expansion.
The existing SDK scanner permits up to 2 GiB of cumulative decoded streams by default.

SOLIDWORKS CLI container inspection supplies a 128 MiB cumulative budget before parsing.
The scanner checks each declared size against the remaining budget before decompression.
The export view independently limits a selected stream to 16 MiB.
Other SDK reading paths retain their existing limits.
A remote process case verifies rejection before inflation using an oversized stream declaration.
See [the scanner](../../../src/convert/adapters/solidworks/container/Container.py) and [CLI view](../../../src/convert/Commands/SolidworksView.py).
