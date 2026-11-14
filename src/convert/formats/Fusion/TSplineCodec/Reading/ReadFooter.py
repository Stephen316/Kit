from dataclasses import replace
from convert.formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger
from convert.formats.Fusion.TSplineCodec.Wire.ReadNumber import ReadNumber


def ReadFooter(Cursor: TextCursor, Header: SurfaceHeader) -> SurfaceHeader:
    Tolerance = ReadNumber(Cursor.ReadFields("tol", 1)[0])
    GeometryTol = ReadNumber(Cursor.ReadFields("geom-tol", 1)[0])
    VersionCount = ReadInteger(Cursor.ReadFields("ver", 1)[0])
    BehaviorVersion = Cursor.ReadFields("behavior-version", 1)[0]
    CompatVersion = Cursor.ReadFields("compat-version", 1)[0]
    if Cursor.Position != len(Cursor.Records):
        raise ValueError("Unsupported trailing TSM records")
    return replace(
        Header,
        Tolerance=Tolerance,
        GeometryTol=GeometryTol,
        VersionCount=VersionCount,
        BehaviorVersion=BehaviorVersion,
        CompatVersion=CompatVersion,
    )
