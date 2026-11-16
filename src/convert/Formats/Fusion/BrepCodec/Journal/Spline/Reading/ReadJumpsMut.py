from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)


# the jumps operation needs a distinct decoding boundary so topology changes retain their native revision relationships
def ReadJumpsMut(Cursor: FieldCursor, Arrays: int) -> tuple[tuple[float, ...], ...]:
    Values: list[tuple[float, ...]] = []
    for _ in range(Arrays):
        Count = ReadCountMut(Cursor, 1024)
        Values.append(tuple(ReadDoubleMut(Cursor) for _ in range(Count)))
    return tuple(Values)
