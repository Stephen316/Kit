from convert.formats.Fusion.MeshCodec.Wire.ProtoBytes import ProtoBytes
from convert.formats.Fusion.MeshCodec.Wire.ProtoField import ProtoField


def ProtoText(Field: ProtoField) -> str:
    Result = ProtoBytes(Field).decode("utf-8")
    if not Result or "\0" in Result or len(Result.encode("utf-8")) > 4096:
        raise ValueError("Invalid Fusion mesh text field")
    return Result
