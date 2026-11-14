from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger
from convert.formats.Fusion.TSplineCodec.Wire.ReadNumber import ReadNumber


def ReadHeader(Cursor: TextCursor) -> SurfaceHeader:
    _ = Cursor.ReadFields("#TS0200", 0)
    Degree = ReadInteger(Cursor.ReadFields("degree", 1)[0])
    CapType = Cursor.ReadFields("cap-type", 1)[0]
    Smoothness = ReadNumber(Cursor.ReadFields("star-smoothness", 1)[0])
    ScaleText, UnitName = Cursor.ReadFields("units", 2)
    Conditions = Cursor.ReadFields("end-conditions", 1)[0]
    KnotRule = Cursor.ReadFields("star-knot-rule", 1)[0]
    return SurfaceHeader(
        Degree,
        CapType,
        Smoothness,
        ReadNumber(ScaleText),
        UnitName,
        Conditions,
        KnotRule,
    )
