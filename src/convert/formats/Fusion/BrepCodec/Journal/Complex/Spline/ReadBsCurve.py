from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsCurve import (
    CheckBsCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckKnots import (
    CheckKnots,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.PoleCount import PoleCount
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.ReadKnotsMut import (
    ReadDegreeMut,
    ReadKnotsMut,
    ReadPolesMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadNameMut import (
    ReadNameMut,
)


def ReadBsBodyMut(Cursor: FieldCursor, NameText: str, Dimension: int) -> BsCurve:
    if NameText not in ("nubs", "nurbs"):
        raise ValueError("Unsupported Fusion B-spline curve form: " + NameText)
    Rational = NameText == "nurbs"
    Degree = ReadDegreeMut(Cursor)
    Closure = ReadLongMut(Cursor, 21)
    Knots, Multiplicity = ReadKnotsMut(Cursor, ReadCountMut(Cursor, 4096))
    CheckKnots(Degree, Closure, Knots, Multiplicity)
    Poles, Weights = ReadPolesMut(
        Cursor, PoleCount(Degree, Multiplicity), Dimension, Rational
    )
    Value = BsCurve(
        Rational, Degree, Closure, Knots, Multiplicity, Dimension, Poles, Weights
    )
    CheckBsCurve(Value, Dimension)
    return Value


def ReadBsCurveMut(Cursor: FieldCursor, Dimension: int) -> BsCurve:
    return ReadBsBodyMut(Cursor, ReadNameMut(Cursor), Dimension)


def ReadBsOptionMut(Cursor: FieldCursor) -> BsCurve | None:
    NameText = ReadNameMut(Cursor)
    if NameText == "nullbs":
        return None
    return ReadBsBodyMut(Cursor, NameText, 2)
