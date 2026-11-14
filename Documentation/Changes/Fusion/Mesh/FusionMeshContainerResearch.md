# Fusion mesh container research

The corpus study now resolves all 103 `.paramesh` members in the indexed 712 Fusion archives. It consumes 141,403 encoded bytes and all 618 streams, resolving 7,691 vertices, 14,935 triangles, octahedral normal tables, corner overrides, feature-edge pairs and face-group assignments. No `.tsm` control-cage member occurs in this indexed set.

[The field model](../../../../re/Fusion/Reconstruction/ParaMesh/WireModel.md) documents the container envelope, protobuf registry, MessagePack stream descriptors, known-length LZMA framing, identity domains and the two distinct delta-coding rules. [The inspection report](../../../../re/Fusion/Reconstruction/ParaMesh/ContainerFields.json) binds every observation to an archive/member digest and records zero inspection failures.

Reproduce the read-only study with Python 3.14 for ZIP method 93:

```shell
uv run --no-project --python 3.14 python re/Fusion/Reconstruction/ParaMesh/InspectContainers.py
```

This command inspects corpus bytes. It does not execute Kit codecs, tests or the native application. The evidence establishes research grammar coverage, not production mesh support, complete archive conversion or native loadability. The local corpus covers three descriptor shapes; raw and split streams, textures and other attribute classes need separate evidence.

See [the compression gotcha](../../../Gotchas/Conversion/Fusion/Geometry/FusionMeshKnownLengthCompression.md). Upstream comparison uses pinned cadmpeg research, attributed in the field model; its Apache-2.0 source and CC-BY-4.0 specification remain separately licensed.
