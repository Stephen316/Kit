from convert.formats.Fusion.DocumentCodec.Values.ReadObjects import (
    ReadInteger,
    ReadObject,
)
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# convert reference needs an explicit validity boundary so model state retains its native feature and ownership relationships
def ConvertRef(Value: object) -> LocalRef | SegmentRef | None:
    if Value is None:
        return None
    Fields = ReadObject(Value)
    if not set(Fields) <= {"entityId", "segmentId"}:
        raise ValueError("Unsupported authored reference fields")
    ObjectId = ReadInteger(Fields["entityId"])
    if "segmentId" in Fields:
        return SegmentRef(ObjectId, ReadInteger(Fields["segmentId"]))
    return LocalRef(ObjectId)
