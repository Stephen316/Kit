from struct import pack as PackValue

from convert.Formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureRefs
from convert.Formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue
from convert.Formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.Formats.Fusion.SegmentCodec.Features.Binary.EmitLocalRef import (
    EmitLocalRef,
)


# the references operation needs a consistent construction rule so native records retain their segment ownership and schema
def EmitRefs(KindValue: FieldKind, Value: KFieldValue) -> bytes:
    if type(Value) is not tuple or len(Value) > KMaxFeatureRefs:
        raise ValueError("Invalid Fusion feature reference collection")
    Encoded = tuple(EmitLocalRef(Entry) for Entry in Value)
    if KindValue is FieldKind.KStrongSet and len(set(Encoded)) != len(Encoded):
        raise ValueError("Duplicate Fusion feature set reference")
    return PackValue("<I", len(Value)) + b"".join(Encoded)
