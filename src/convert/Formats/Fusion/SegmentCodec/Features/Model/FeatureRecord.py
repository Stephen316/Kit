from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.Formats.Fusion.SegmentCodec.Features.Model.FeatureFrame import FeatureFrame
from convert.Formats.Fusion.SegmentCodec.Features.Model.FeatureGroup import FeatureGroup


# feature record needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class FeatureRecord:
    Lineage: tuple[ClassStamp, ...]
    Frame: FeatureFrame
    Groups: tuple[FeatureGroup, ...]
