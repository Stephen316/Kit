from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)


def ReadPointsMut(
    Cursor: FieldCursor, Count: int, Width: int
) -> tuple[tuple[float, ...], ...]:
    return tuple(
        tuple(ReadDoubleMut(Cursor) for _ in range(Width)) for _ in range(Count)
    )
