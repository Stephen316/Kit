from struct import pack as PackValue

from convert.Formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


# the local reference operation needs a consistent construction rule so native records retain their segment ownership and schema
def EmitLocalRef(Value: KFieldValue) -> bytes:
    if Value is None:
        return b"\0"
    if (
        not isinstance(Value, LocalRef)
        or type(Value.ObjectId) is not int
        or not 0 <= Value.ObjectId < 1 << 64
    ):
        raise ValueError("Invalid Fusion feature local reference")
    return PackValue("<BQH", 1, Value.ObjectId, 0)
