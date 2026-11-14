from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsSurface import (
    CheckBsSurface,
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


def ReadSurfaceMut(Cursor: FieldCursor) -> BsSurface:
    NameText = ReadNameMut(Cursor)
    if NameText not in ("nubs", "nurbs"):
        raise ValueError("Unsupported Fusion B-spline surface form: " + NameText)
    Rational = NameText == "nurbs"
    UDegree = ReadDegreeMut(Cursor)
    VDegree = ReadDegreeMut(Cursor)
    RationalForm = ReadNameMut(Cursor) if Rational else ""
    UClosure, VClosure, USingular, VSingular = (
        ReadLongMut(Cursor, 21) for _ in range(4)
    )
    UCount = ReadCountMut(Cursor, 4096)
    VCount = ReadCountMut(Cursor, 4096)
    UKnots, UMultiplicity = ReadKnotsMut(Cursor, UCount)
    VKnots, VMultiplicity = ReadKnotsMut(Cursor, VCount)
    CheckKnots(UDegree, UClosure, UKnots, UMultiplicity)
    CheckKnots(VDegree, VClosure, VKnots, VMultiplicity)
    Count = PoleCount(UDegree, UMultiplicity) * PoleCount(VDegree, VMultiplicity)
    Poles, Weights = ReadPolesMut(Cursor, Count, 3, Rational)
    Value = BsSurface(
        Rational,
        RationalForm,
        UDegree,
        VDegree,
        UClosure,
        VClosure,
        USingular,
        VSingular,
        UKnots,
        UMultiplicity,
        VKnots,
        VMultiplicity,
        Poles,
        Weights,
    )
    CheckBsSurface(Value)
    return Value
