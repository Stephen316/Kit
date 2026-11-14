from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.SplineEval import (
    PointOnCurve,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CheckFormParts import (
    CheckClamped,
    CheckRegions,
    CheckWindows,
    IsFiniteNumber,
    IsFormLabel,
    IsNumberTuple,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormSurface,
    FormUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

KPointSlack = 1e-6


def IsNearPoint(PoleValue: tuple[float, ...], Point: tuple[float, ...]) -> bool:
    return (
        max(
            abs(LeftValue - RightValue)
            for LeftValue, RightValue in zip(PoleValue, Point, strict=True)
        )
        <= KPointSlack
    )


def FormBounds(Value: FormEdge) -> tuple[float, float]:
    Knots = Value.Curve.Knots
    if Value.Bounds is None:
        return (Knots[0], Knots[-1])
    if not IsNumberTuple(Value.Bounds, 2) or not (
        Knots[0] <= Value.Bounds[0] < Value.Bounds[1] <= Knots[-1]
    ):
        raise ValueError("Converted Form edge bounds must lie inside its curve")
    return Value.Bounds


def CheckFormEdge(Value: FormEdge, Model: FormBody, FaceCount: int) -> None:
    if not isinstance(CastValue(object, Value), FormEdge):
        raise ValueError("Converted Form edge must be typed")
    Count = len(Model.PointsCm)
    EndPoints = (Value.StartVertex, Value.EndVertex)
    if any(type(Vertex) is not int or not 0 <= Vertex < Count for Vertex in EndPoints):
        raise ValueError("Converted Form edge names a missing vertex")
    if Value.StartVertex == Value.EndVertex and Value.Curve.Closure == 0:
        raise ValueError("Converted Form closed edges need a closed curve")
    CheckClamped(Value.Curve, 3)
    Bounds = FormBounds(Value)
    for Parameter, Vertex in zip(Bounds, EndPoints, strict=True):
        if not IsNearPoint(
            PointOnCurve(Value.Curve, Parameter), Model.PointsCm[Vertex]
        ):
            raise ValueError("Converted Form edge curve misses its vertices")
    if type(Value.Jumps) is not tuple or len(Value.Jumps) != 3:
        raise ValueError("Converted Form edge needs three discontinuity lists")
    if not all(IsNumberTuple(Jumps) for Jumps in Value.Jumps):
        raise ValueError("Converted Form edge discontinuities must be finite")
    Convexity = Value.Convexity
    if (
        type(Convexity) is not str
        or not Convexity
        or not Convexity.isascii()
        or not Convexity.isprintable()
    ):
        raise ValueError("Converted Form edge convexity must be printable text")
    if not IsFormLabel(Value.Label) or bool(Value.Label) != bool(Value.Windows):
        raise ValueError("Converted Form edge label and windows disagree")
    CheckWindows(Value.Windows, FaceCount)


def CheckFormSurf(Value: FormSurface, RegionCount: int) -> None:
    if not isinstance(CastValue(object, Value), FormSurface):
        raise ValueError("Converted Form face surface must be typed")
    if not isinstance(CastValue(object, Value.Cache), NubsSurface):
        raise ValueError("Converted Form surface cache must be a NUBS surface")
    if type(Value.Region) is not int or not 0 <= Value.Region < RegionCount:
        raise ValueError("Converted Form surface names a missing patch program")
    if type(Value.Jumps) is not tuple or len(Value.Jumps) != 6:
        raise ValueError("Converted Form surface needs six discontinuity lists")
    if not all(IsNumberTuple(Jumps) for Jumps in Value.Jumps):
        raise ValueError("Converted Form surface discontinuities must be finite")


def CheckFormUse(Value: FormUse, Model: FormBody) -> FormEdge:
    if not isinstance(CastValue(object, Value), FormUse):
        raise ValueError("Converted Form coedge must be typed")
    if type(Value.EdgeIndex) is not int or not 0 <= Value.EdgeIndex < len(Model.Edges):
        raise ValueError("Converted Form coedge names a missing edge")
    if type(Value.Reversed) is not bool:
        raise ValueError("Converted Form coedge sense must be boolean")
    if not IsFiniteNumber(Value.Fit) or Value.Fit < 0.0:
        raise ValueError("Converted Form pcurve fit must be finite")
    EdgeValue = Model.Edges[Value.EdgeIndex]
    CheckClamped(Value.Pcurve, 2)
    Range = (EdgeValue.Curve.Knots[0], EdgeValue.Curve.Knots[-1])
    if (Value.Pcurve.Knots[0], Value.Pcurve.Knots[-1]) != Range:
        raise ValueError("Converted Form pcurve range differs from its edge curve")
    return EdgeValue


def CheckFormFace(Value: FormFace, Model: FormBody) -> None:
    if not isinstance(CastValue(object, Value), FormFace):
        raise ValueError("Converted Form face must be typed")
    CheckFormSurf(Value.Surface, len(Model.Regions))
    if type(Value.Uses) is not tuple or not Value.Uses:
        raise ValueError("Converted Form face needs one coedge loop")
    Edges = tuple(CheckFormUse(UseValue, Model) for UseValue in Value.Uses)
    Heads = tuple(
        EdgeValue.StartVertex if UseValue.Reversed else EdgeValue.EndVertex
        for UseValue, EdgeValue in zip(Value.Uses, Edges)
    )
    Tails = tuple(
        EdgeValue.EndVertex if UseValue.Reversed else EdgeValue.StartVertex
        for UseValue, EdgeValue in zip(Value.Uses, Edges)
    )
    if Heads != Tails[1:] + Tails[:1]:
        raise ValueError("Converted Form coedge loop is not closed")
    if type(
        CastValue(object, Value.DoubleSided)
    ) is not bool or Value.Contained not in (
        None,
        True,
        False,
    ):
        raise ValueError("Converted Form face sidedness flags are invalid")
    if not IsFormLabel(Value.Label):
        raise ValueError("Converted Form face label must be a positive integer")


def CheckFormUsage(Model: FormBody) -> None:
    Senses: dict[int, list[bool]] = {}
    for FaceValue in Model.Faces:
        for UseValue in FaceValue.Uses:
            Senses.setdefault(UseValue.EdgeIndex, []).append(UseValue.Reversed)
    if set(Senses) != set(range(len(Model.Edges))):
        raise ValueError("Converted Form body has an edge without coedges")
    if any(
        len(Flags) > 2 or len(Flags) != len(set(Flags)) for Flags in Senses.values()
    ):
        raise ValueError("Converted Form edges need one or two opposed coedges")
    Touched = {
        Vertex
        for EdgeValue in Model.Edges
        for Vertex in (EdgeValue.StartVertex, EdgeValue.EndVertex)
    }
    if Touched != set(range(len(Model.PointsCm))):
        raise ValueError("Converted Form body has an isolated vertex")
    Labels = [FaceValue.Label for FaceValue in Model.Faces if FaceValue.Label]
    Pieces = {
        EdgeValue.Label: (EdgeValue.Curve, EdgeValue.Windows)
        for EdgeValue in Model.Edges
        if EdgeValue.Label
    }
    Labels += list(Pieces)
    IsShared = all(
        Pieces[EdgeValue.Label] == (EdgeValue.Curve, EdgeValue.Windows)
        for EdgeValue in Model.Edges
        if EdgeValue.Label
    )
    if len(set(Labels)) != len(Labels) or not IsShared:
        raise ValueError("Converted Form labels must be unique")
    Regions = [FaceValue.Surface.Region for FaceValue in Model.Faces]
    if len(set(Regions)) != len(Regions):
        raise ValueError("Converted Form faces must own distinct patch programs")


def CheckFormBody(Model: FormBody, Surface: TsplineSurface) -> None:
    if not isinstance(CastValue(object, Model), FormBody):
        raise ValueError("A typed converted Form body is required")
    if not isinstance(CastValue(object, Surface), TsplineSurface):
        raise ValueError("A typed T-spline cage is required")
    FaceCount = len(Surface.Topology.Faces)
    if type(Model.PointsCm) is not tuple or not all(
        IsNumberTuple(Point, 3) for Point in Model.PointsCm
    ):
        raise ValueError("Converted Form points must be finite triples")
    for Field in (Model.Edges, Model.Faces):
        if type(Field) is not tuple or not Field:
            raise ValueError("Converted Form body needs edges and faces")
    CheckRegions(Model.Regions, FaceCount)
    for EdgeValue in Model.Edges:
        CheckFormEdge(EdgeValue, Model, FaceCount)
    for FaceValue in Model.Faces:
        CheckFormFace(FaceValue, Model)
    CheckFormUsage(Model)
