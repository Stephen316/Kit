from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Features.Model.ClassStamp import ClassStamp
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldSpec import FieldSpec


@MakeDataClass(frozen=True, slots=True)
class ClassLayout:
    Stamp: ClassStamp
    Members: tuple[FieldSpec, ...]
