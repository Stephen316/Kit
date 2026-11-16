from dataclasses import replace
from convert.Formats.Fusion.TSplineCodec.Model.SurfaceHeader import SurfaceHeader
from convert.Formats.Fusion.TSplineCodec.Wire.TextCursor import TextCursor
from convert.Formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger
from convert.Formats.Fusion.TSplineCodec.Wire.ReadNumber import ReadNumber


# the footer operation needs a distinct decoding boundary so control cage topology retains its native connectivity
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
