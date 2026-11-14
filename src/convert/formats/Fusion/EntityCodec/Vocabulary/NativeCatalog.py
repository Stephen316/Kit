from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.NamedType import NamedType


@MakeDataClass(frozen=True, slots=True)
class NativeCatalog:
    Classes: Mapping[str, tuple[ClassSchema, ...]]
    NamedTypes: tuple[NamedType, ...]
