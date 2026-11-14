from convert.formats.Fusion.BrepCodec.Journal.Spline.Capped.CappedShape import (
    CappedShape,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Caps.SolveCaps import SolveCaps
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.CheckFolds import (
    CheckFolds,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
    FormFace,
    FormSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Poles.CapHook import KCapHook
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageResult import (
    CageResult,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ClassifyEdges import (
    ClassifyEdges,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import (
    CageParts,
)
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface


def ShapeEdges(Shape: CappedShape, Result: CageResult) -> tuple[FormEdge, ...]:
    return tuple(
        FormEdge(
            EdgeValue.StartVertex,
            EdgeValue.EndVertex,
            Result.Curves[EdgeValue.CurveIndex],
            Result.CurveJumps[EdgeValue.CurveIndex],
            EdgeValue.Convexity,
            EdgeValue.Label,
            EdgeValue.Windows,
            EdgeValue.Bounds,
        )
        for EdgeValue in Shape.Edges
    )


def ShapeFaces(Shape: CappedShape, Result: CageResult) -> tuple[FormFace, ...]:
    Found = {FaceValue.FaceIndex: FaceValue for FaceValue in Result.Faces}
    if set(Found) != {FaceValue.Region for FaceValue in Shape.Faces}:
        raise ValueError("Fusion Form conversion found faces without poles")
    return tuple(
        FormFace(
            FormSurface(
                Found[FaceValue.Region].Surface,
                Found[FaceValue.Region].Jumps,
                FaceValue.Region,
            ),
            FaceValue.Uses,
            FaceValue.Label,
            FaceValue.DoubleSided,
            FaceValue.Contained,
        )
        for FaceValue in Shape.Faces
    )


def ShapeBody(Surface: TsplineSurface, CapSolver: KCapHook = SolveCaps) -> FormBody:
    Shape, Result = CageParts(Surface, CapSolver)
    if len(Result.Points) != len(Shape.Points):
        raise ValueError("Fusion Form conversion found vertices without poles")
    return FormBody(
        Result.Points,
        ShapeEdges(Shape, Result),
        ShapeFaces(Shape, Result),
        Shape.Regions,
    )


def CageBody(Surface: TsplineSurface, CapSolver: KCapHook = SolveCaps) -> FormBody:
    BodyValue = ClassifyEdges(ShapeBody(Surface, CapSolver))
    CheckFolds(BodyValue)
    return BodyValue
