import math

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.FormBody import (
    FormBody,
    FormEdge,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ClassifyEdges import (
    CrossValue,
)
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import (
    CurveFrame,
    SurfaceFrame,
)

KFoldCosine = 0.5
KFoldSamples = 4


def SpanParams(Values: list[float]) -> list[float]:
    return [
        Begin + (Finish - Begin) * (Index + 0.5) / KFoldSamples
        for Begin, Finish in zip(Values, Values[1:])
        for Index in range(KFoldSamples)
    ]


def IsBent(First: list[float], Second: list[float]) -> bool:
    Inner = sum(Former * Latter for Former, Latter in zip(First, Second))
    Lengths = math.sqrt(
        sum(Entry * Entry for Entry in First) * sum(Entry * Entry for Entry in Second)
    )
    return Lengths == 0.0 or Inner <= KFoldCosine * Lengths


def FaceNormals(Cache: NubsSurface) -> list[list[list[float]]]:
    ParamsU = SpanParams([KnotValue.Value for KnotValue in Cache.KnotsU])
    ParamsV = SpanParams([KnotValue.Value for KnotValue in Cache.KnotsV])
    return [
        [CrossValue(*SurfaceFrame(Cache, ParamU, ParamV)) for ParamU in ParamsU]
        for ParamV in ParamsV
    ]


def IsFolded(Normals: list[list[list[float]]]) -> bool:
    Pairs = [
        (RowValue[Index], RowValue[Index + 1])
        for RowValue in Normals
        for Index in range(len(RowValue) - 1)
    ]
    Pairs += [
        (Lower[Index], Upper[Index])
        for Lower, Upper in zip(Normals, Normals[1:])
        for Index in range(len(Lower))
    ]
    return any(IsBent(First, Second) for First, Second in Pairs)


def IsBackward(EdgeValue: FormEdge) -> bool:
    Knots = EdgeValue.Curve.Knots
    Lower, Upper = EdgeValue.Bounds or (Knots[0], Knots[-1])
    Breaks = [Lower, *(Value for Value in Knots if Lower < Value < Upper), Upper]
    Tangents = [CurveFrame(EdgeValue.Curve, Param)[1] for Param in SpanParams(Breaks)]
    return any(IsBent(First, Second) for First, Second in zip(Tangents, Tangents[1:]))


def CheckFolds(BodyValue: FormBody) -> None:
    for FaceValue in BodyValue.Faces:
        if IsFolded(FaceNormals(FaceValue.Surface.Cache)):
            raise ValueError("Fusion Form conversion would find a folded face")
    if any(IsBackward(EdgeValue) for EdgeValue in BodyValue.Edges):
        raise ValueError("Fusion Form conversion would find a folded edge")
