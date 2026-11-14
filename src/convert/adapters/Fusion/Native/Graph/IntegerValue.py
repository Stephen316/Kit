from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


def IntegerValue(Value: KEntityValue) -> int:
    if type(Value) is not int:
        raise ValueError("Native Fusion semantic field requires an integer")
    return Value
