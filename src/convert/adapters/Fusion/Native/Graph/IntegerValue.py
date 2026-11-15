from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue


# integer value needs an explicit validity boundary so public document claims remain grounded in native records
def IntegerValue(Value: KEntityValue) -> int:
    if type(Value) is not int:
        raise ValueError("Native Fusion semantic field requires an integer")
    return Value
