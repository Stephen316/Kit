from convert.formats.Fusion.MeshCodec.Wire.ByteCursor import ByteCursor


def ReadVarint(Cursor: ByteCursor) -> int:
    Result = 0
    for Shift in range(0, 70, 7):
        Number = Cursor.Integer(1)
        if Shift == 63 and Number > 1:
            raise ValueError("Fusion mesh varint exceeds uint64")
        Result |= (Number & 127) << Shift
        if Number < 128:
            if Shift and not Number:
                raise ValueError("Noncanonical Fusion mesh varint")
            return Result
    raise ValueError("Unterminated Fusion mesh varint")
