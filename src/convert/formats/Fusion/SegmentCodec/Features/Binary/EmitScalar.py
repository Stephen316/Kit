from math import isfinite as IsFinite
from struct import pack as PackValue

from convert.formats.Fusion.SegmentCodec.Features.Model.FieldValue import KFieldValue
from convert.formats.Fusion.SegmentCodec.Features.Schema.FieldKind import FieldKind
from convert.formats.Fusion.SegmentCodec.Features.Binary.ScalarKinds import KScalarKinds


def EmitScalar(KindValue: FieldKind, Value: KFieldValue) -> bytes:
    CodeValue = KScalarKinds[KindValue][0]
    Lower, Upper = KScalarKinds[KindValue][2:]
    if KindValue is FieldKind.KBoolean:
        if type(Value) is not bool:
            raise ValueError("Fusion feature boolean requires bool")
    elif KindValue is FieldKind.KDecimal:
        if type(Value) is not int and type(Value) is not float:
            raise ValueError("Fusion feature double requires a number")
        if not IsFinite(Value):
            raise ValueError("Fusion feature double requires a finite number")
    elif type(Value) is not int or not Lower <= Value <= Upper:
        raise ValueError("Fusion feature integer is outside its wire range")
    return PackValue("<" + CodeValue, Value)
