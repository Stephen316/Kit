# Drawing Zstandard frames depend on the encoder build

Modern F2D members use ZIP method 93, which is Zstandard.
Kit reproduces the observed frames with these encoder settings.

| Setting            | Value |
| ------------------ | ----- |
| Compression level  | 3     |
| Checksum flag      | 1     |
| Content size flag  | 0     |

These settings reproduced every frame of the three Kit controls with Python 3.14 and `libzstd` 1.5.7.
A different `libzstd` build can choose different matches at the same level.
The frame then still decodes to the same payload, but the archive bytes differ.

`EmitDrawing` takes the encoder as the `CompressZstd` argument.
Without an encoder, it writes valid raw Zstandard blocks.
The integration tests replay the frames that the reader observed.
This makes the byte-exact checks independent of the `libzstd` build on the test host.
