from struct import pack as PackValue

from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.EntityCodec.Model.SegmentRef import SegmentRef
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitLocalRef import EmitLocalRef
from convert.formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef


def EmitCrossRef(Value: CrossRef) -> bytes:
    if (
        type(Value.ObjectId) is not int
        or type(Value.Token) is not int
        or type(Value.TypeGuid) is not str
        or not 0 <= Value.ObjectId < 1 << 64
        or not 0 <= Value.Token < 1 << 64
        or len(Value.TypeGuid) not in (36, 37)
        or not Value.TypeGuid.isascii()
        or not Value.TypeGuid.isprintable()
    ):
        raise ValueError("Invalid Fusion cross-document reference")
    TypeText = Value.TypeGuid.encode("ascii")
    return (
        PackValue("<BQBQBI", 1, Value.ObjectId, 1, Value.Token, 0, len(TypeText))
        + TypeText
        + b"\0"
    )


def EmitReference(Value: KEntityValue) -> bytes:
    if Value is None or isinstance(Value, LocalRef):
        return EmitLocalRef(Value)
    if isinstance(Value, CrossRef):
        return EmitCrossRef(Value)
    if not isinstance(Value, SegmentRef) or type(Value.ObjectId) is not int or type(Value.SegmentId) is not int:
        raise ValueError("Invalid Fusion entity reference type")
    if not 0 <= Value.ObjectId < 1 << 64 or not 0 <= Value.SegmentId < 1 << 32:
        raise ValueError("Fusion entity reference identity exceeds wire range")
    return PackValue("<BQBBI", 1, Value.ObjectId, 0, 1, Value.SegmentId)
