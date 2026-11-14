from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureFrame import FeatureFrame
from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureGroup import FeatureGroup


@MakeDataClass(frozen=True, slots=True)
class FeatureRecord:
    Lineage: tuple[ClassStamp, ...]
    Frame: FeatureFrame
    Groups: tuple[FeatureGroup, ...]
