from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor


def ReadRows(
    Cursor: TextCursor, KindValue: str, FieldCount: int
) -> tuple[tuple[str, ...], ...]:
    Result: list[tuple[str, ...]] = []
    while Cursor.HasKind(KindValue):
        Result.append(Cursor.ReadFields(KindValue, FieldCount))
    return tuple(Result)
