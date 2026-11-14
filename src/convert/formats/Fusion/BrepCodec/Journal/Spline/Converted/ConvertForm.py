from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import (
    ConvertGrid,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CheckFolds import (
    CheckFolds,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.GridBody import GridBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import CageBody
from convert.formats.Fusion.TSplineCodec.Model.KnotSurface import KnotSurface
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface
from convert.formats.Fusion.TSplineCodec.Validation.CheckSurface import CheckSurface


def HasCompounds(Surface: TsplineSurface) -> bool:
    return len(Surface.Grips) > len(Surface.Topology.Vertices)


def HasInnerCreases(Surface: TsplineSurface) -> bool:
    Creases = Surface.Creases
    if Creases is None:
        return False
    RimEdges = {
        LinkValue.EdgeIndex
        for LinkValue in Surface.Topology.Links
        if LinkValue.FaceIndex == -1
    }
    return not set(Creases.EdgeIndices) <= RimEdges


def IsPlainKnots(Surface: TsplineSurface) -> bool:
    Intervals = tuple(EdgeValue.KnotInterval for EdgeValue in Surface.Topology.Edges)
    return not isinstance(Surface, KnotSurface) or Surface.EdgeKnots == Intervals


def ConvertForm(Surface: TsplineSurface) -> FormBody:
    CheckSurface(Surface)
    if not IsPlainKnots(Surface):
        raise ValueError("Fusion Form conversion has no rule for edge knot records")
    if not HasCompounds(Surface) or HasInnerCreases(Surface):
        return CageBody(Surface)
    BodyValue = GridBody(ConvertGrid(Surface))
    CheckFolds(BodyValue)
    return BodyValue
