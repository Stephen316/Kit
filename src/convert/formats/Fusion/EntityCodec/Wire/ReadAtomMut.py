from math import isfinite as IsFinite
from struct import unpack as UnpackValue

from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.AtomKinds import KAtomKinds, KSharedKinds
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.Binary.ReadScalar import ReadScalarMut


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
