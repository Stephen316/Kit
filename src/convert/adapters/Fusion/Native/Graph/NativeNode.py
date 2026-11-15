from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.EntityGroup import EntityGroup
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# native node needs an explicit state contract so public document claims remain grounded in native records
@MakeDataClass(frozen=True, slots=True)
class NativeNode:
    SegmentId: int
    ObjectId: int
    ClassName: str
    Groups: tuple[EntityGroup[KEntityValue], ...]
    Frame: EntityFrame

    # the fields contract needs a shared interpretation so public document claims remain grounded in native records
    @property
    def Fields(self) -> dict[str, KEntityValue]:
        return {
            Field.FieldName: Field.Value
            for Group in self.Groups
            for Field in Group.Fields
        }

    # the identity contract needs a shared interpretation so public document claims remain grounded in native records
    @property
    def Identity(self) -> str:
        return f"fusion:{self.SegmentId}:{self.ObjectId}"
