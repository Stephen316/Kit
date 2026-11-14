from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Schema.FieldSpec import FieldSpec
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType


@MakeDataClass(frozen=True, slots=True)
class ClassSchema:
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
    Members: tuple[FieldSpec[WireType], ...]
    IsValue: bool = False
    IsOpaque: bool = False
