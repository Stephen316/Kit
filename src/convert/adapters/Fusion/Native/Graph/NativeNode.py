from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


@MakeDataClass(frozen=True, slots=True)
class NativeNode:
    SegmentId: int
    ObjectId: int
    ClassName: str
    Groups: tuple[EntityGroup[KEntityValue], ...]
    Frame: EntityFrame

    @property
    def Fields(self) -> dict[str, KEntityValue]:
        return {
            Field.FieldName: Field.Value
            for Group in self.Groups
            for Field in Group.Fields
        }

    @property
    def Identity(self) -> str:
        return f"fusion:{self.SegmentId}:{self.ObjectId}"
