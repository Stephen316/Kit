from convert.formats.Fusion.MeshCodec.Wire.ByteCursor import ByteCursor
from convert.formats.Fusion.MeshCodec.Wire.ReadMapAtom import ReadMapAtom


def ReadMap(Payload: bytes) -> dict[str, int | bool]:
    Cursor = ByteCursor(Payload)
    CodeValue = Cursor.Integer(1)
    if 128 <= CodeValue <= 143:
        Count = CodeValue - 128
    elif CodeValue in (222, 223):
        Count = Cursor.Integer(2 if CodeValue == 222 else 4, "big")
    else:
        raise ValueError("Expected Fusion mesh MessagePack map")
    if Count > 16:
        raise ValueError("Unsupported Fusion mesh map size")
    Result: dict[str, int | bool] = {}
    for _ in range(Count):
        KeyName, Value = ReadMapAtom(Cursor), ReadMapAtom(Cursor)
        if not isinstance(KeyName, str) or not KeyName or KeyName in Result:
            raise ValueError("Invalid Fusion mesh MessagePack key")
        if not isinstance(Value, int):
            raise ValueError("Unsupported Fusion mesh MessagePack value")
        Result[KeyName] = Value
    if Cursor.Remaining():
        raise ValueError("Trailing Fusion mesh MessagePack bytes")
    return Result
