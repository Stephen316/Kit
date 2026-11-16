from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue


# feature field needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class FeatureField:
    NameText: str
    Value: KFieldValue
