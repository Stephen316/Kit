from dataclasses import dataclass as MakeDataClass
from itertools import accumulate as Accumulate

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
    NurbsEdge,
    NurbsFace,
    NurbsUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface


@MakeDataClass(frozen=True, slots=True)
class NurbsLayout:
    FaceBase: int
    LoopBase: int
    SurfaceBase: int
    CoedgeBase: int
    EdgeBase: int
    VertexBase: int
    PointBase: int
    PcurveBase: int
    CurveBase: int
    LoopStarts: tuple[int, ...]
    UseStarts: tuple[int, ...]
    LoopFaces: tuple[int, ...]
    UseLoops: tuple[int, ...]
    PcurveSlots: tuple[int, ...]
    TableSlots: tuple[int, ...]
    EntityCount: int


def FaceLoops(FaceSpec: NurbsFace) -> tuple[tuple[NurbsUse, ...], ...]:
    return (FaceSpec.Uses, *FaceSpec.Holes)


def EdgeRange(EdgeSpec: NurbsEdge) -> tuple[float, float]:
    if EdgeSpec.Bounds is None:
        return EdgeSpec.Curve.Knots[0], EdgeSpec.Curve.Knots[-1]
    return EdgeSpec.Bounds


def ModelUses(Model: NurbsBody) -> tuple[NurbsUse, ...]:
    return tuple(
        UseSpec
        for FaceSpec in Model.Faces
        for LoopUses in FaceLoops(FaceSpec)
        for UseSpec in LoopUses
    )


def MakeNurbsLayout(Model: NurbsBody) -> NurbsLayout:
    FaceCount = len(Model.Faces)
    LoopList = tuple(
        (FaceIndex, LoopUses)
        for FaceIndex, FaceSpec in enumerate(Model.Faces)
        for LoopUses in FaceLoops(FaceSpec)
    )
    LoopStarts = (0, *Accumulate(1 + len(FaceSpec.Holes) for FaceSpec in Model.Faces))
    UseStarts = (0, *Accumulate(len(LoopUses) for _, LoopUses in LoopList))
    UseLoops = tuple(
        LoopIndex for LoopIndex, (_, LoopUses) in enumerate(LoopList) for _ in LoopUses
    )
    UseList = ModelUses(Model)
    Ordinals = tuple(Accumulate(int(UseSpec.Pcurve is not None) for UseSpec in UseList))
    PcurveSlots = tuple(
        Ordinal - 1 if UseSpec.Pcurve is not None else -1
        for UseSpec, Ordinal in zip(UseList, Ordinals, strict=True)
    )
    Splines = tuple(
        Accumulate(
            int(isinstance(FaceSpec.Surface, BsSurface)) for FaceSpec in Model.Faces
        )
    )
    TableSlots = tuple(
        Count - 1 if isinstance(FaceSpec.Surface, BsSurface) else -1
        for FaceSpec, Count in zip(Model.Faces, Splines, strict=True)
    )
    LoopBase = 4 + FaceCount
    SurfaceBase = LoopBase + len(LoopList)
    CoedgeBase = SurfaceBase + FaceCount
    EdgeBase = CoedgeBase + len(UseList)
    VertexBase = EdgeBase + len(Model.Edges)
    PointBase = VertexBase + len(Model.PointsCm)
    PcurveBase = PointBase + len(Model.PointsCm)
    CurveBase = PcurveBase + (Ordinals[-1] if Ordinals else 0)
    return NurbsLayout(
        4,
        LoopBase,
        SurfaceBase,
        CoedgeBase,
        EdgeBase,
        VertexBase,
        PointBase,
        PcurveBase,
        CurveBase,
        LoopStarts,
        UseStarts,
        tuple(FaceIndex for FaceIndex, _ in LoopList),
        UseLoops,
        PcurveSlots,
        TableSlots,
        CurveBase + len(Model.Edges),
    )
