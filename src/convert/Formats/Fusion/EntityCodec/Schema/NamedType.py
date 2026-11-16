from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType


# named type needs an explicit state contract so entity identifiers retain their schema and reference meaning
@MakeDataClass(frozen=True, slots=True)
class NamedType:
    TypeName: str
    ValueType: WireType
