from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue


@MakeDataClass(frozen=True, slots=True)
class FeatureField:
    NameText: str
    Value: KFieldValue
