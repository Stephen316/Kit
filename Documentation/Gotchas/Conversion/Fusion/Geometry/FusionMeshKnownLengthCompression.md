# Mesh LZMA termination depends on the declared size

The `.paramesh` stream header contains a decoded byte count and the selector `5d 14`. Treating the following bytes as an unknown-length raw LZMA stream and probing one extra output byte made eight valid corpus members appear oversized.

The format carries a known output length. Reconstruct a standard LZMA-alone header using properties `5d`, the dictionary size and the declared uint64 output size. All 618 streams in the 103-member corpus then terminate exactly with no unused input. The count is part of decompressor framing, not merely an assertion after unbounded expansion.

Production handling must still enforce input and output bounds and reject malformed or trailing data. Discarding extra output or accepting arbitrary decoder errors is not the correction.

The [research model](../../../../../re/Fusion/Reconstruction/ParaMesh/WireModel.md) records the failed hypothesis and the exact successful framing. [Member-level evidence](../../../../../re/Fusion/Reconstruction/ParaMesh/ContainerFields.json) records source digests and decoded stream lengths. This research does not establish a production mesh writer or native acceptance.
