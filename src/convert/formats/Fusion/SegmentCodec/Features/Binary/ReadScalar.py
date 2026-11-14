from math import isfinite as IsFinite
from struct import unpack as UnpackValue

from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Binary.ScalarKinds import KScalarKinds


def ReadScalarMut(Cursor: MetaCursor, KindValue: FieldKind) -> bool | int | float:
    CodeValue, Width, Lower, Upper = KScalarKinds[KindValue]
    RawValue = UnpackValue("<" + CodeValue, Cursor.TakeBytes(Width))[0]
    if KindValue is FieldKind.KDecimal:
        Number = float(RawValue)
        if not IsFinite(Number):
            raise ValueError("Nonfinite Fusion feature number")
        return Number
    Number = int(RawValue)
    if not Lower <= Number <= Upper:
        raise ValueError("Invalid Fusion feature scalar")
    return bool(Number) if KindValue is FieldKind.KBoolean else Number
