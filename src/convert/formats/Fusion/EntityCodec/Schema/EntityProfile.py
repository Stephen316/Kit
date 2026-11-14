from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.ExternalTarget import ExternalTarget
from convert.formats.Fusion.EntityCodec.Schema.NamedType import NamedType


@MakeDataClass(frozen=True, slots=True)
class EntityProfile:
    RootGuid: str
    Classes: tuple[ClassSchema, ...]
    ExternalTargets: tuple[ExternalTarget, ...] = ()
    NamedTypes: tuple[NamedType, ...] = ()
