from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)


def ReadKnotsMut(
    Cursor: FieldCursor, Count: int
) -> tuple[tuple[float, ...], tuple[int, ...]]:
    Pairs = tuple(
        (ReadDoubleMut(Cursor), ReadCountMut(Cursor, 26)) for _ in range(Count)
    )
    return tuple(KnotValue for KnotValue, _ in Pairs), tuple(
        Multiple for _, Multiple in Pairs
    )


def ReadPolesMut(
    Cursor: FieldCursor, Count: int, Width: int, Rational: bool
) -> tuple[tuple[tuple[float, ...], ...], tuple[float, ...]]:
    if not 0 < Count <= 65536:
        raise ValueError("Fusion B-spline pole table exceeds its bounds")
    Stride = Width + (1 if Rational else 0)
    Values = tuple(ReadDoubleMut(Cursor) for _ in range(Count * Stride))
    Poles = tuple(
        Values[Index * Stride : Index * Stride + Width] for Index in range(Count)
    )
    Weights = tuple(
        Values[Index * Stride + Width] for Index in range(Count) if Rational
    )
    return Poles, Weights


def ReadDegreeMut(Cursor: FieldCursor) -> int:
    Degree = ReadLongMut(Cursor)
    if not 1 <= Degree <= 25:
        raise ValueError("Unsupported Fusion B-spline degree")
    return Degree
