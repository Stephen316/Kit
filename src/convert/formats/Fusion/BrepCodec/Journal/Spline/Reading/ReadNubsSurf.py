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
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.CountPoles import (
    CountPoles,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadKnotsMut import (
    ReadKnotsMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Reading.ReadPointsMut import (
    ReadPointsMut,
)


def ReadNubsSurf(Cursor: FieldCursor) -> NubsSurface:
    NameText = ReadNameMut(Cursor)
    if NameText not in ("nubs", "nurbs"):
        raise ValueError("Unsupported Fusion journal qualified field")
    IsRational = NameText == "nurbs"
    DegreeU = ReadLongMut(Cursor)
    DegreeV = ReadLongMut(Cursor)
    FormName = ReadNameMut(Cursor) if IsRational else ""
    Shape = tuple(ReadLongMut(Cursor, 21) for _ in range(4))
    CountU = ReadCountMut(Cursor, 1024)
    CountV = ReadCountMut(Cursor, 1024)
    KnotsU = ReadKnotsMut(Cursor, CountU)
    KnotsV = ReadKnotsMut(Cursor, CountV)
    Total = CountPoles(KnotsU, DegreeU) * CountPoles(KnotsV, DegreeV)
    if Total > 65536:
        raise ValueError("Fusion spline surface control net exceeds its quota")
    Entries = ReadPointsMut(Cursor, Total, 4 if IsRational else 3)
    Points = tuple((Entry[0], Entry[1], Entry[2]) for Entry in Entries)
    Weights = tuple(Entry[3] for Entry in Entries) if IsRational else ()
    if IsRational and min(Weights) <= 0.0:
        raise ValueError("Fusion spline surface weight is not positive")
    return NubsSurface(
        DegreeU,
        DegreeV,
        Shape[0],
        Shape[1],
        Shape[2],
        Shape[3],
        KnotsU,
        KnotsV,
        Points,
        Weights,
        FormName,
    )
