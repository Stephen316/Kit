from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


@MakeDataClass(frozen=True, slots=True)
class NamedType:
    TypeName: str
    ValueType: WireType
