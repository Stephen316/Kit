from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


@MakeDataClass(frozen=True, slots=True)
class EntityRecord:
    ObjectId: int
    TypeCode: int
    IsPrimary: bool
    Frame: EntityFrame
    Groups: tuple[EntityGroup[KEntityValue], ...]
