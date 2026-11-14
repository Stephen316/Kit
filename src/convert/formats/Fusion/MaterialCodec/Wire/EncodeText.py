from struct import pack as PackValue

from convert.formats.Fusion.MaterialCodec.Limits import KMaxString


def EncodeText(Value: str) -> bytes:
    if type(Value) is not str:
        raise ValueError("Fusion material text must be a string")
    Encoded = Value.encode("utf-8")
    if len(Encoded) > KMaxString:
        raise ValueError("Fusion material text exceeds the size limit")
    return PackValue("<I", len(Encoded)) + Encoded
