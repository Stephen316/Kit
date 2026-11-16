from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec


# class layout needs an explicit state contract so native records retain their segment ownership and schema
@MakeDataClass(frozen=True, slots=True)
class ClassLayout:
    Stamp: ClassStamp
    Members: tuple[FieldSpec, ...]
