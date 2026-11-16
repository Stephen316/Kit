from convert.Formats.Fusion.MeshCodec.Wire.ByteCursor import ByteCursor


# the chunk operation needs a distinct decoding boundary so vertex and index streams retain their intended connectivity
def ReadChunk(Cursor: ByteCursor, Expected: int) -> bytes:
    Length = Cursor.Integer(8)
    if Length > 64 * 1024 * 1024:
        raise ValueError("Fusion mesh chunk allocation exceeds limit")
    if Cursor.Integer(4) != Expected:
        raise ValueError("Unexpected Fusion mesh chunk kind or order")
    return Cursor.TakeBytes(Length)
