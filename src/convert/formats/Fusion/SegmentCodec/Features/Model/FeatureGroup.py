from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Features.Model.FeatureField import FeatureField


@MakeDataClass(frozen=True, slots=True)
class FeatureGroup:
    ClassGuid: str
    Fields: tuple[FeatureField, ...]
