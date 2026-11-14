from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)


def FrameIndex(Value: KEntityValue, Owners: dict[int, EntityRecord], Frame: int) -> int:
    Target = Owners.get(Value.ObjectId) if isinstance(Value, LocalRef) else None
    if Target is None:
        raise ValueError("Control frame list names no primary entity")
    Fields = GroupFields(Target.Groups)
    Owner = Fields.get("rMesh")
    Index = Fields.get("tsID")
    if not isinstance(Owner, LocalRef) or Owner.ObjectId != Frame:
        raise ValueError("Control frame entity is owned by another frame")
    if type(Index) is not int:
        raise ValueError("Control frame entity has no T-spline index")
    return Index
