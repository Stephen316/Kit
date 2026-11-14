from math import isfinite as IsFinite
from struct import pack as PackValue

from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.AtomKinds import KAtomKinds, KSharedKinds
from convert.formats.Fusion.SegmentCodec.Features.Binary.EmitScalar import EmitScalar


def EmitAtom(Value: KEntityValue, Shape: WireType) -> bytes:
    Format, _, Lower, Upper = KAtomKinds[Shape.KindValue]
    if Shape.KindValue in ("f32", "f64"):
        if type(Value) not in (int, float) or not isinstance(Value, (int, float)):
            raise ValueError("Fusion entity floating scalar requires a number")
        try:
            Numeric = float(Value)
        except OverflowError:
            raise ValueError("Fusion entity scalar exceeds binary64 range") from None
        if not IsFinite(Numeric) or (Shape.KindValue == "f32" and abs(Numeric) > 3.4028234663852886e38):
            raise ValueError("Fusion entity floating scalar is nonfinite or out of range")
        return PackValue("<" + Format, Numeric)
    if Shape.KindValue == "bool":
        if type(Value) is not bool:
            raise ValueError("Fusion entity flag requires a boolean")
    elif type(Value) is not int or not Lower <= Value <= Upper:
        raise ValueError("Fusion entity integer exceeds its wire range")
    if Shape.AllowedInts and Value not in Shape.AllowedInts:
        raise ValueError("Unsupported Fusion entity integer discriminator")
    if Shape.KindValue in KSharedKinds:
        return EmitScalar(KSharedKinds[Shape.KindValue], Value)
    return PackValue("<" + Format, Value)
