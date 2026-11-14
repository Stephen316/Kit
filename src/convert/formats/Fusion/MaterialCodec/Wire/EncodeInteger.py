from struct import pack as PackValue


def EncodeInteger(Value: int) -> bytes:
    if type(Value) is not int or not -(1 << 31) <= Value < (1 << 31):
        raise ValueError("Fusion material integer exceeds signed 32-bit range")
    return PackValue("<i", Value)
