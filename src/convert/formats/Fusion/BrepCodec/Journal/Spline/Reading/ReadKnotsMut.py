from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineKnot import SplineKnot


# the knots operation needs a distinct decoding boundary so topology changes retain their native revision relationships
def ReadKnotsMut(Cursor: FieldCursor, Count: int) -> tuple[SplineKnot, ...]:
    return tuple(
        SplineKnot(ReadDoubleMut(Cursor), ReadLongMut(Cursor)) for _ in range(Count)
    )
