from convert.formats.Fusion.EntityCodec.Model.EntityRecord import EntityRecord
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def MeshReference(
    Value: KEntityValue, Owners: dict[int, EntityRecord], ClassGuid: str
) -> EntityRecord:
    if not isinstance(Value, (LocalRef, SegmentRef)) or (
        isinstance(Value, SegmentRef) and Value.SegmentId != 0
    ):
        raise ValueError("Mesh link requires a local Design entity reference")
    Target = Owners.get(Value.ObjectId)
    if (
        Target is None
        or not Target.IsPrimary
        or not Target.Groups
        or Target.Groups[0].ClassGuid.upper() != ClassGuid
    ):
        raise ValueError("Mesh reference has no compatible primary entity")
    return Target
