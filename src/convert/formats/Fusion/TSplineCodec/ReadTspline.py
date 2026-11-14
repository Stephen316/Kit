from convert.formats.Fusion.TSplineCodec.Model.KnotSurface import KnotSurface
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Model.ControlGrip import ControlGrip
from convert.formats.Fusion.TSplineCodec.Wire.MakeCursor import MakeCursor
from convert.formats.Fusion.TSplineCodec.Wire.ReadRows import ReadRows
from convert.formats.Fusion.TSplineCodec.Wire.ReadNumber import ReadNumber
from convert.formats.Fusion.TSplineCodec.Wire.ReadInteger import ReadInteger
from convert.formats.Fusion.TSplineCodec.Reading.ReadHeader import ReadHeader
from convert.formats.Fusion.TSplineCodec.Reading.ReadFooter import ReadFooter
from convert.formats.Fusion.TSplineCodec.Reading.ReadTopology import ReadTopology
from convert.formats.Fusion.TSplineCodec.Reading.ReadMapping import ReadMapping
from convert.formats.Fusion.TSplineCodec.Reading.ReadCreases import ReadCreases
from convert.formats.Fusion.TSplineCodec.Reading.ReadSymmetry import ReadSymmetry
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


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
