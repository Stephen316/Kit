from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor


def MakeCursor(Payload: bytes) -> TextCursor:
    if len(Payload) > 67108864:
        raise ValueError("TSM file exceeds the allocation limit")
    TextValue = Payload.decode("ascii")
    if any(ord(Letter) < 32 and Letter not in "\n\r\t" for Letter in TextValue):
        raise ValueError("TSM contains unsupported control characters")
    Records = tuple(
        tuple(LineText.split())
        for LineText in TextValue.splitlines()
        if LineText.strip()
    )
    if not Records or len(Records) > 1000000:
        raise ValueError("TSM record allocation is invalid")
    return TextCursor(Records)
