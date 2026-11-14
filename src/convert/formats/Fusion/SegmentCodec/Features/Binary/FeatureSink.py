from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureBytes
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


class FeatureSink(MetaSink):
    __slots__ = ()

    def __init__(self) -> None:
        super().__init__(KMaxFeatureBytes)
