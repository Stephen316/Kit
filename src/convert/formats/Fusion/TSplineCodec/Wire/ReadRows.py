from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor


# the rows operation needs a distinct decoding boundary so control cage topology retains its native connectivity
def ReadRows(
    Cursor: TextCursor, KindValue: str, FieldCount: int
) -> tuple[tuple[str, ...], ...]:
    Result: list[tuple[str, ...]] = []
    while Cursor.HasKind(KindValue):
        Result.append(Cursor.ReadFields(KindValue, FieldCount))
    return tuple(Result)
