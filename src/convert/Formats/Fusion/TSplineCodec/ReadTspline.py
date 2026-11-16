from convert.Formats.Fusion.TSplineCodec.Model.KnotSurface import KnotSurface
from convert.Formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.Formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.Formats.Fusion.TSplineCodec.Wire.MakeCursor import MakeCursor
from convert.Formats.Fusion.TSplineCodec.Wire.ReadRows import ReadRows
from convert.Formats.Fusion.TSplineCodec.Wire.ReadNumber import ReadNumber
from convert.Formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger
from convert.Formats.Fusion.TSplineCodec.Reading.ReadHeader import ReadHeader
from convert.Formats.Fusion.TSplineCodec.Reading.ReadFooter import ReadFooter
from convert.Formats.Fusion.TSplineCodec.Reading.ReadTopology import ReadTopology
from convert.Formats.Fusion.TSplineCodec.Reading.ReadMapping import ReadMapping
from convert.Formats.Fusion.TSplineCodec.Reading.ReadCreases import ReadCreases
from convert.Formats.Fusion.TSplineCodec.Reading.ReadSymmetry import ReadSymmetry
from convert.Formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


# the tspline operation needs a distinct decoding boundary so control cage topology retains its native connectivity
def ReadTspline(Payload: bytes) -> TsplineSurface:
    Cursor = MakeCursor(Payload)
    Header = ReadHeader(Cursor)
    Topology = ReadTopology(Cursor)
    Mapping = ReadMapping(Cursor)
    Grips = tuple(
        ControlGrip(*(ReadNumber(Value) for Value in Fields))
        for Fields in ReadRows(Cursor, "0g", 4)
    )
    Creases = ReadCreases(Cursor)
    Symmetry = ReadSymmetry(Cursor)
    EdgeKnots = tuple(ReadNumber(Fields[0]) for Fields in ReadRows(Cursor, "106ek", 1))
    SmartGrips = tuple(
        ReadInteger(Fields[0]) for Fields in ReadRows(Cursor, "50000grip", 1)
    )
    Members = (
        ReadFooter(Cursor, Header),
        Topology,
        Grips,
        Mapping,
        Creases,
        Symmetry,
        SmartGrips,
    )
    Result = KnotSurface(*Members, EdgeKnots) if EdgeKnots else TsplineSurface(*Members)
    CheckSurface(Result)
    return Result
