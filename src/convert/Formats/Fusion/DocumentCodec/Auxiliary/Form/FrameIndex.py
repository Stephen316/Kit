from convert.Formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from convert.Formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.Formats.Fusion.DocumentCodec.Reading.Materials.GroupFields import (
    GroupFields,
)


# frame index needs an explicit validity boundary so supporting records retain their owning document relationships
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
