from math import isfinite as IsFinite
from struct import unpack as UnpackValue

from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.AtomKinds import KAtomKinds, KSharedKinds
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.Binary.ReadScalar import ReadScalarMut


# the atom operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadAtomMut(Cursor: MetaCursor, Shape: WireType) -> bool | int | float:
    if Shape.KindValue in KSharedKinds:
        Value = ReadScalarMut(Cursor, KSharedKinds[Shape.KindValue])
    else:
        Format, Width, _, _ = KAtomKinds[Shape.KindValue]
        RawValue = UnpackValue("<" + Format, Cursor.TakeBytes(Width))[0]
        Value = float(RawValue) if Shape.KindValue == "f32" else int(RawValue)
    if isinstance(Value, float) and not IsFinite(Value):
        raise ValueError("Nonfinite Fusion entity scalar")
    if Shape.AllowedInts and Value not in Shape.AllowedInts:
        raise ValueError("Unsupported Fusion entity integer discriminator")
    return Value
