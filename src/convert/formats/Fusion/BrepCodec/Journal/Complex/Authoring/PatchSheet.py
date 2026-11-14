from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
    NurbsEdge,
    NurbsFace,
    NurbsUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.CheckBsSurface import (
    CheckBsSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.PoleCount import (
    PoleCount,
)


def BoundaryCurve(Surface: BsSurface, SideIndex: int) -> BsCurve:
    CheckBsSurface(Surface)
    UCount = PoleCount(Surface.UDegree, Surface.UMultiplicity)
    VCount = PoleCount(Surface.VDegree, Surface.VMultiplicity)
    Selections = {
        0: range(UCount),
        1: range(UCount - 1, UCount * VCount, UCount),
        2: range((VCount - 1) * UCount, VCount * UCount),
        3: range(0, UCount * VCount, UCount),
    }
    if SideIndex not in Selections:
        raise ValueError("Fusion patch boundary side must be 0, 1, 2 or 3")
    Indices = tuple(Selections[SideIndex])
    AlongU = SideIndex in (0, 2)
    return BsCurve(
        Surface.Rational,
        Surface.UDegree if AlongU else Surface.VDegree,
        0,
        Surface.UKnots if AlongU else Surface.VKnots,
        Surface.UMultiplicity if AlongU else Surface.VMultiplicity,
        3,
        tuple(Surface.Poles[Index] for Index in Indices),
        tuple(Surface.Weights[Index] for Index in Indices) if Surface.Rational else (),
    )


def LinePcurve(
    StartPoint: tuple[float, float],
    EndPoint: tuple[float, float],
    Lower: float,
    Upper: float,
) -> BsCurve:
    return BsCurve(False, 1, 0, (Lower, Upper), (1, 1), 2, (StartPoint, EndPoint), ())


def PatchSheet(Surface: BsSurface, EntityTag: int = -1) -> NurbsBody:
    CheckBsSurface(Surface)
    if Surface.UClosure or Surface.VClosure or Surface.USingular or Surface.VSingular:
        raise ValueError("Fusion patch sheet requires an open nonsingular surface")
    ULower, UUpper = Surface.UKnots[0], Surface.UKnots[-1]
    VLower, VUpper = Surface.VKnots[0], Surface.VKnots[-1]
    Curves = tuple(BoundaryCurve(Surface, SideIndex) for SideIndex in range(4))
    Corners = (
        Curves[0].Poles[0],
        Curves[0].Poles[-1],
        Curves[2].Poles[-1],
        Curves[2].Poles[0],
    )
    Edges = (
        NurbsEdge(0, 1, Curves[0]),
        NurbsEdge(1, 2, Curves[1]),
        NurbsEdge(3, 2, Curves[2]),
        NurbsEdge(0, 3, Curves[3]),
    )
    LoopUses = (
        NurbsUse(
            0, False, LinePcurve((ULower, VLower), (UUpper, VLower), ULower, UUpper)
        ),
        NurbsUse(
            1, False, LinePcurve((UUpper, VLower), (UUpper, VUpper), VLower, VUpper)
        ),
        NurbsUse(
            2, True, LinePcurve((ULower, VUpper), (UUpper, VUpper), ULower, UUpper)
        ),
        NurbsUse(
            3, True, LinePcurve((ULower, VLower), (ULower, VUpper), VLower, VUpper)
        ),
    )
    return NurbsBody(
        tuple((Corner[0], Corner[1], Corner[2]) for Corner in Corners),
        Edges,
        (NurbsFace(Surface, LoopUses),),
        EntityTag,
    )
