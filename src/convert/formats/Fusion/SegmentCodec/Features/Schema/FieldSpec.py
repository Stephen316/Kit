from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind


@MakeDataClass(frozen=True, slots=True)
class FieldSpec:
    NameText: str
    WireKind: FieldKind
    FlagMask: int = 0x33
