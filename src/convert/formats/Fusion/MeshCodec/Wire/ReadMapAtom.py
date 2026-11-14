from convert.formats.Fusion.MeshCodec.Wire.ByteCursor import ByteCursor


def ReadMapAtom(Cursor: ByteCursor) -> str | int | bool:
    CodeValue = Cursor.Integer(1)
    if CodeValue < 128:
        return CodeValue
    if CodeValue in (194, 195):
        return CodeValue == 195
    if 160 <= CodeValue <= 191:
        return Cursor.TakeBytes(CodeValue - 160).decode("utf-8")
    if CodeValue in (217, 218, 219):
        Length = Cursor.Integer({217: 1, 218: 2, 219: 4}[CodeValue], "big")
        if Length > 4096:
            raise ValueError("Oversized Fusion mesh MessagePack text")
        return Cursor.TakeBytes(Length).decode("utf-8")
    if CodeValue in (204, 205, 206, 207):
        return Cursor.Integer({204: 1, 205: 2, 206: 4, 207: 8}[CodeValue], "big")
    raise ValueError("Unsupported Fusion mesh MessagePack atom")
