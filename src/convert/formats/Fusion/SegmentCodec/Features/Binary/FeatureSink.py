from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureBytes
from convert.formats.Fusion.SegmentCodec.Metadata.MetaSink import MetaSink


# the feature sink contract needs a dedicated boundary so native records retain their segment ownership and schema
class FeatureSink(MetaSink):
    __slots__ = ()

    # feature sink needs explicit initial state so native records retain their segment ownership and schema
    def __init__(self) -> None:
        super().__init__(KMaxFeatureBytes)
