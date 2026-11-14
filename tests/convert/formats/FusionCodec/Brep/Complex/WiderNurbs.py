from math import sqrt as SquareRoot

from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    CylinderCarrier,
    NurbsBody,
    NurbsEdge,
    NurbsFace,
    NurbsUse,
    PlaneCarrier,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.PatchSheet import (
    BoundaryCurve,
    LinePcurve,
    PatchSheet,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.SplineEval import (
    DeBoorPoint,
    FullKnots,
    Homogeneous,
    PointOnSurface,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.PoleCount import PoleCount
from convert.formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from tests.convert.formats.FusionCodec.Brep.Complex.NurbsSamples import BicubicPatch

KHalfRoot = SquareRoot(0.5)
KCircleSquare = (
    (1.0, 0.0),
    (1.0, 1.0),
    (0.0, 1.0),
    (-1.0, 1.0),
    (-1.0, 0.0),
    (-1.0, -1.0),
    (0.0, -1.0),
    (1.0, -1.0),
    (1.0, 0.0),
)
KCircleWeights = (1.0, KHalfRoot, 1.0, KHalfRoot, 1.0, KHalfRoot, 1.0, KHalfRoot, 1.0)
KCircleKnots = (0.0, 0.25, 0.5, 0.75, 1.0)
KCircleCounts = (2, 2, 2, 2, 2)
KHoleBox = (0.3, 0.6, 0.35, 0.65)
KTubeProfile = ((1.0, 0.0), (1.4, 0.6), (0.8, 1.4), (1.0, 2.0))
KDomeProfile = ((1.0, 1.5), (1.0, 2.1), (0.55, 2.5), (0.0, 2.5))
KTorusMajor = 2.0
KTorusMinor = 0.5
KApexRows = (
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.4), (2.0, 0.0, 0.3), (3.0, 0.0, 0.0)),
    ((0.3, 0.8, 0.5), (1.1, 0.9, 1.0), (1.9, 0.9, 0.9), (2.7, 0.8, 0.4)),
    ((0.9, 1.6, 0.8), (1.3, 1.7, 1.2), (1.7, 1.7, 1.1), (2.1, 1.6, 0.7)),
    ((1.5, 2.4, 1.0), (1.5, 2.4, 1.0), (1.5, 2.4, 1.0), (1.5, 2.4, 1.0)),
)


def SpacePoint(Values: tuple[float, ...]) -> KJournalVector:
    return (Values[0], Values[1], Values[2])


def PeriodLine(
    StartPoint: tuple[float, float], EndPoint: tuple[float, float]
) -> BsCurve:
    return BsCurve(False, 1, 2, (0.0, 1.0), (1, 1), 2, (StartPoint, EndPoint), ())


def UnitLine(StartPoint: tuple[float, float], EndPoint: tuple[float, float]) -> BsCurve:
    return LinePcurve(StartPoint, EndPoint, 0.0, 1.0)


def CircleCurve(Radius: float, Height: float) -> BsCurve:
    return BsCurve(
        True,
        2,
        2,
        KCircleKnots,
        KCircleCounts,
        3,
        tuple(
            (Radius * Corner[0], Radius * Corner[1], Height) for Corner in KCircleSquare
        ),
        KCircleWeights,
    )


def ProfileCurve(Profile: tuple[tuple[float, float], ...]) -> BsCurve:
    return BsCurve(
        False,
        3,
        0,
        (0.0, 1.0),
        (3, 3),
        3,
        tuple((Radius, 0.0, Height) for Radius, Height in Profile),
        (),
    )


def CubicRevolved(
    Profile: tuple[tuple[float, float], ...], VSingular: int
) -> BsSurface:
    return BsSurface(
        True,
        "both",
        2,
        3,
        2,
        0,
        0,
        VSingular,
        KCircleKnots,
        KCircleCounts,
        (0.0, 1.0),
        (3, 3),
        tuple(
            (Radius * Corner[0], Radius * Corner[1], Height)
            for Radius, Height in Profile
            for Corner in KCircleSquare
        ),
        tuple(Weight for _ in Profile for Weight in KCircleWeights),
    )


def TorusSurface() -> BsSurface:
    Profile = tuple(
        (KTorusMajor + KTorusMinor * Corner[0], KTorusMinor * Corner[1])
        for Corner in KCircleSquare
    )
    return BsSurface(
        True,
        "both",
        2,
        2,
        2,
        2,
        0,
        0,
        KCircleKnots,
        KCircleCounts,
        KCircleKnots,
        KCircleCounts,
        tuple(
            (Radius * Corner[0], Radius * Corner[1], Height)
            for Radius, Height in Profile
            for Corner in KCircleSquare
        ),
        tuple(
            UWeight * VWeight
            for VWeight in KCircleWeights
            for UWeight in KCircleWeights
        ),
    )


def IsoCurve(Surface: BsSurface, AlongU: bool, FixedValue: float) -> BsCurve:
    UCount = PoleCount(Surface.UDegree, Surface.UMultiplicity)
    Weighted = Homogeneous(Surface.Poles, Surface.Weights)
    PoleRows = tuple(
        Weighted[Start : Start + UCount] for Start in range(0, len(Weighted), UCount)
    )
    if AlongU:
        Strands = tuple(
            tuple(PoleRow[Index] for PoleRow in PoleRows) for Index in range(UCount)
        )
        LiftRows = tuple(
            DeBoorPoint(
                Surface.VDegree,
                FullKnots(Surface.VKnots, Surface.VMultiplicity),
                Strand,
                FixedValue,
            )
            for Strand in Strands
        )
        Degree, Knots, Counts = Surface.UDegree, Surface.UKnots, Surface.UMultiplicity
    else:
        LiftRows = tuple(
            DeBoorPoint(
                Surface.UDegree,
                FullKnots(Surface.UKnots, Surface.UMultiplicity),
                PoleRow,
                FixedValue,
            )
            for PoleRow in PoleRows
        )
        Degree, Knots, Counts = Surface.VDegree, Surface.VKnots, Surface.VMultiplicity
    return BsCurve(
        Surface.Rational,
        Degree,
        0,
        Knots,
        Counts,
        3,
        tuple(
            tuple(Number / Lifted[-1] for Number in Lifted[:-1]) for Lifted in LiftRows
        ),
        tuple(Lifted[-1] for Lifted in LiftRows) if Surface.Rational else (),
    )


def HoledPatch() -> NurbsBody:
    Surface = BicubicPatch()
    Sheet = PatchSheet(Surface)
    ULower, UUpper, VLower, VUpper = KHoleBox
    Corners = ((ULower, VLower), (UUpper, VLower), (UUpper, VUpper), (ULower, VUpper))
    HoleEdges = (
        NurbsEdge(4, 5, IsoCurve(Surface, True, VLower), (ULower, UUpper)),
        NurbsEdge(5, 6, IsoCurve(Surface, False, UUpper), (VLower, VUpper)),
        NurbsEdge(7, 6, IsoCurve(Surface, True, VUpper), (ULower, UUpper)),
        NurbsEdge(4, 7, IsoCurve(Surface, False, ULower), (VLower, VUpper)),
    )
    HoleUses = (
        NurbsUse(
            7, False, LinePcurve((ULower, VLower), (ULower, VUpper), VLower, VUpper)
        ),
        NurbsUse(
            6, False, LinePcurve((ULower, VUpper), (UUpper, VUpper), ULower, UUpper)
        ),
        NurbsUse(
            5, True, LinePcurve((UUpper, VLower), (UUpper, VUpper), VLower, VUpper)
        ),
        NurbsUse(
            4, True, LinePcurve((ULower, VLower), (UUpper, VLower), ULower, UUpper)
        ),
    )
    return NurbsBody(
        (
            *Sheet.PointsCm,
            *(SpacePoint(PointOnSurface(Surface, *Corner)) for Corner in Corners),
        ),
        (*Sheet.Edges, *HoleEdges),
        (NurbsFace(Surface, Sheet.Faces[0].Uses, (HoleUses,)),),
    )


def ApexSurface() -> BsSurface:
    return BsSurface(
        False,
        "",
        3,
        3,
        0,
        0,
        0,
        2,
        (0.0, 1.0),
        (3, 3),
        (0.0, 1.0),
        (3, 3),
        tuple(Point for PoleRow in KApexRows for Point in PoleRow),
        (),
    )


def CollapsedPatch() -> NurbsBody:
    Surface = ApexSurface()
    return NurbsBody(
        (KApexRows[0][0], KApexRows[0][-1], KApexRows[-1][0]),
        (
            NurbsEdge(0, 1, BoundaryCurve(Surface, 0)),
            NurbsEdge(1, 2, BoundaryCurve(Surface, 1)),
            NurbsEdge(0, 2, BoundaryCurve(Surface, 3)),
        ),
        (
            NurbsFace(
                Surface,
                (
                    NurbsUse(0, False, UnitLine((0.0, 0.0), (1.0, 0.0))),
                    NurbsUse(1, False, UnitLine((1.0, 0.0), (1.0, 1.0))),
                    NurbsUse(2, True, UnitLine((0.0, 0.0), (0.0, 1.0))),
                ),
            ),
        ),
    )


def SeamUses(
    LowerEdge: int, SeamEdge: int, UpperEdge: int | None
) -> tuple[NurbsUse, ...]:
    LeadUses = (
        NurbsUse(LowerEdge, False, PeriodLine((0.0, 0.0), (1.0, 0.0))),
        NurbsUse(SeamEdge, False, UnitLine((0.0, 0.0), (0.0, 1.0)), 1.0),
    )
    TrailUse = NurbsUse(SeamEdge, True, UnitLine((0.0, 0.0), (0.0, 1.0)))
    if UpperEdge is None:
        return (*LeadUses, TrailUse)
    return (
        *LeadUses,
        NurbsUse(UpperEdge, True, PeriodLine((0.0, 1.0), (1.0, 1.0))),
        TrailUse,
    )


def CappedTube() -> NurbsBody:
    Bottom, Upper = KTubeProfile[0], KTubeProfile[-1]
    return NurbsBody(
        ((Bottom[0], 0.0, Bottom[1]), (Upper[0], 0.0, Upper[1])),
        (
            NurbsEdge(0, 0, CircleCurve(*Bottom)),
            NurbsEdge(1, 1, CircleCurve(*Upper)),
            NurbsEdge(0, 1, ProfileCurve(KTubeProfile)),
        ),
        (
            NurbsFace(CubicRevolved(KTubeProfile, 0), SeamUses(0, 2, 1)),
            NurbsFace(
                PlaneCarrier((0.0, 0.0, Bottom[1]), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)),
                (NurbsUse(0, True, None),),
            ),
            NurbsFace(
                PlaneCarrier((0.0, 0.0, Upper[1]), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
                (NurbsUse(1, False, None),),
            ),
        ),
    )


def DomedCylinder() -> NurbsBody:
    RimPoint, ApexPoint = KDomeProfile[0], KDomeProfile[-1]
    return NurbsBody(
        (
            (RimPoint[0], 0.0, 0.0),
            (RimPoint[0], 0.0, RimPoint[1]),
            (ApexPoint[0], 0.0, ApexPoint[1]),
        ),
        (
            NurbsEdge(0, 0, CircleCurve(RimPoint[0], 0.0)),
            NurbsEdge(1, 1, CircleCurve(*RimPoint)),
            NurbsEdge(1, 2, ProfileCurve(KDomeProfile)),
        ),
        (
            NurbsFace(
                CylinderCarrier(
                    (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (RimPoint[0], 0.0, 0.0)
                ),
                (NurbsUse(0, False, None),),
                ((NurbsUse(1, True, None),),),
            ),
            NurbsFace(
                PlaneCarrier((0.0, 0.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)),
                (NurbsUse(0, True, None),),
            ),
            NurbsFace(CubicRevolved(KDomeProfile, 2), SeamUses(1, 2, None)),
        ),
    )


def NurbsTorus() -> NurbsBody:
    Outer = KTorusMajor + KTorusMinor
    MinorCircle = BsCurve(
        True,
        2,
        2,
        KCircleKnots,
        KCircleCounts,
        3,
        tuple(
            (KTorusMajor + KTorusMinor * Corner[0], 0.0, KTorusMinor * Corner[1])
            for Corner in KCircleSquare
        ),
        KCircleWeights,
    )
    return NurbsBody(
        ((Outer, 0.0, 0.0),),
        (NurbsEdge(0, 0, CircleCurve(Outer, 0.0)), NurbsEdge(0, 0, MinorCircle)),
        (
            NurbsFace(
                TorusSurface(),
                (
                    NurbsUse(0, False, PeriodLine((0.0, 0.0), (1.0, 0.0))),
                    NurbsUse(1, False, PeriodLine((0.0, 0.0), (0.0, 1.0)), 1.0),
                    NurbsUse(0, True, PeriodLine((0.0, 0.0), (1.0, 0.0)), 0.0, 1.0),
                    NurbsUse(1, True, PeriodLine((0.0, 0.0), (0.0, 1.0))),
                ),
            ),
        ),
    )


def WiderModels() -> tuple[tuple[str, NurbsBody], ...]:
    return (
        ("HoledPatch", HoledPatch()),
        ("CollapsedPatch", CollapsedPatch()),
        ("CappedTube", CappedTube()),
        ("DomedCylinder", DomedCylinder()),
        ("NurbsTorus", NurbsTorus()),
    )
