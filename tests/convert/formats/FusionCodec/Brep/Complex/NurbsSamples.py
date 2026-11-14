from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.NurbsBody import (
    NurbsBody,
    NurbsEdge,
    NurbsFace,
    NurbsUse,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.PatchSheet import (
    LinePcurve,
    PatchSheet,
)
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsSurface import BsSurface
from convert.formats.Fusion.BrepCodec.Models.HistoryState import HistoryState
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp

KNurbsHistory = HistoryState(7, 2, 7, 1, 2, 7)
KNurbsStamp = GeometryStamp(
    "Kit independent NURBS author", "ASM 232.5.0.65535 OSX", "Thu Nov 12 00:00:00 2026"
)
KPillowSide = 2.0
KPillowOrigin = (0.5, 0.25, -0.75)
KPillowAxes = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}
KPillowFaces = (
    ((0, 0, 0), "y", "x", 0.25, 1.0, False),
    ((0, 0, 1), "x", "y", 0.5, 1.8, True),
    ((0, 0, 0), "x", "z", 0.35, 1.0, False),
    ((0, 1, 0), "z", "x", 0.35, 1.0, False),
    ((0, 0, 0), "z", "y", 0.35, 1.0, False),
    ((1, 0, 0), "y", "z", 0.35, 1.0, False),
)
KPatchHeights = (
    (0.0, 0.2, 0.1, -0.1, 0.0),
    (0.3, 0.9, 1.1, 0.6, 0.2),
    (0.1, 0.7, 1.4, 0.8, -0.2),
    (0.0, -0.1, 0.3, 0.2, 0.1),
)
KPatchShifts = {(1, 2): (0.15, 0.0), (2, 3): (0.0, -0.1)}
KRationalHeights = (
    (0.0, 0.3, 0.1),
    (0.2, 1.0, 0.4),
    (0.4, 1.3, 0.2),
    (0.1, 0.2, 0.0),
)
KRationalWeights = (
    (1.0, 0.8, 1.0),
    (0.9, 0.6, 0.9),
    (1.1, 0.7, 1.2),
    (1.0, 0.85, 1.0),
)


def GrevilleGrid(
    Degree: int, Knots: tuple[float, ...], Counts: tuple[int, ...]
) -> tuple[float, ...]:
    Expanded = [
        KnotValue for KnotValue, Repeat in zip(Knots, Counts) for _ in range(Repeat)
    ]
    Vector = (
        [Knots[0]] * (Degree + 1 - Counts[0])
        + Expanded
        + [Knots[-1]] * (Degree + 1 - Counts[-1])
    )
    Averages: list[float] = []
    for Index in range(len(Vector) - Degree - 1):
        Total = 0.0
        for Offset in range(1, Degree + 1):
            Total += Vector[Index + Offset]
        Averages.append(Total / Degree)
    return tuple(Averages)


def BicubicPatch() -> BsSurface:
    UGrid = GrevilleGrid(3, (0.0, 0.4, 1.0), (3, 1, 3))
    VGrid = GrevilleGrid(3, (0.0, 1.0), (3, 3))
    Poles: list[tuple[float, float, float]] = []
    for RowIndex, VValue in enumerate(VGrid):
        for ColumnIndex, UValue in enumerate(UGrid):
            ShiftX, ShiftY = KPatchShifts.get((RowIndex, ColumnIndex), (0.0, 0.0))
            Poles.append(
                (
                    0.5 + 3.0 * UValue + ShiftX,
                    -1.0 + 2.0 * VValue + ShiftY,
                    KPatchHeights[RowIndex][ColumnIndex],
                )
            )
    return BsSurface(
        False,
        "",
        3,
        3,
        0,
        0,
        0,
        0,
        (0.0, 0.4, 1.0),
        (3, 1, 3),
        (0.0, 1.0),
        (3, 3),
        tuple(Poles),
        (),
    )


def RationalPatch() -> BsSurface:
    Poles = tuple(
        (
            -2.0 + 1.5 * ColumnIndex,
            1.0 + 1.2 * RowIndex,
            KRationalHeights[RowIndex][ColumnIndex],
        )
        for RowIndex in range(4)
        for ColumnIndex in range(3)
    )
    Weights = tuple(
        KRationalWeights[RowIndex][ColumnIndex]
        for RowIndex in range(4)
        for ColumnIndex in range(3)
    )
    return BsSurface(
        True,
        "both",
        2,
        2,
        0,
        0,
        0,
        0,
        (0.0, 1.0),
        (2, 2),
        (0.0, 0.5, 1.0),
        (2, 1, 2),
        Poles,
        Weights,
    )


def CornerPoint(Corner: tuple[int, int, int]) -> tuple[float, float, float]:
    return (
        KPillowOrigin[0] + KPillowSide * Corner[0],
        KPillowOrigin[1] + KPillowSide * Corner[1],
        KPillowOrigin[2] + KPillowSide * Corner[2],
    )


def CornerIndex(Corner: tuple[int, int, int]) -> int:
    return Corner[0] + 2 * Corner[1] + 4 * Corner[2]


def PillowEdges() -> tuple[NurbsEdge, ...]:
    Edges: list[NurbsEdge] = []
    for AxisIndex in range(3):
        Others = [Index for Index in range(3) if Index != AxisIndex]
        for FirstSide in (0, 1):
            for SecondSide in (0, 1):
                Start = [0, 0, 0]
                Start[Others[0]], Start[Others[1]] = FirstSide, SecondSide
                Finish = list(Start)
                Finish[AxisIndex] = 1
                StartCorner = (Start[0], Start[1], Start[2])
                FinishCorner = (Finish[0], Finish[1], Finish[2])
                StartPoint, FinishPoint = CornerPoint(StartCorner), CornerPoint(
                    FinishCorner
                )
                Poles = tuple(
                    tuple(
                        StartPoint[Coordinate]
                        + (FinishPoint[Coordinate] - StartPoint[Coordinate])
                        * StepIndex
                        / 3
                        for Coordinate in range(3)
                    )
                    for StepIndex in range(4)
                )
                Curve = BsCurve(False, 3, 0, (0.0, 1.0), (3, 3), 3, Poles, ())
                Edges.append(
                    NurbsEdge(
                        CornerIndex(StartCorner), CornerIndex(FinishCorner), Curve
                    )
                )
    return tuple(Edges)


def PillowSurface(
    Origin: tuple[int, int, int],
    UName: str,
    VName: str,
    Bulge: float,
    Weight: float,
    Split: bool,
) -> BsSurface:
    UAxis, VAxis = KPillowAxes[UName], KPillowAxes[VName]
    Normal = (
        UAxis[1] * VAxis[2] - UAxis[2] * VAxis[1],
        UAxis[2] * VAxis[0] - UAxis[0] * VAxis[2],
        UAxis[0] * VAxis[1] - UAxis[1] * VAxis[0],
    )
    UKnots, UCounts = ((0.0, 0.5, 1.0), (3, 1, 3)) if Split else ((0.0, 1.0), (3, 3))
    UGrid, VGrid = GrevilleGrid(3, UKnots, UCounts), GrevilleGrid(3, (0.0, 1.0), (3, 3))
    Poles: list[tuple[float, ...]] = []
    Weights: list[float] = []
    for RowIndex, VValue in enumerate(VGrid):
        for ColumnIndex, UValue in enumerate(UGrid):
            Interior = (
                0 < RowIndex < len(VGrid) - 1 and 0 < ColumnIndex < len(UGrid) - 1
            )
            BasePoint = [
                KPillowOrigin[AxisIndex]
                + KPillowSide
                * (
                    Origin[AxisIndex]
                    + UValue * UAxis[AxisIndex]
                    + VValue * VAxis[AxisIndex]
                )
                for AxisIndex in range(3)
            ]
            Poles.append(
                tuple(
                    BasePoint[AxisIndex]
                    + (Bulge * Normal[AxisIndex] if Interior else 0.0)
                    for AxisIndex in range(3)
                )
            )
            Weights.append(Weight if Interior else 1.0)
    Rational = Weight != 1.0
    return BsSurface(
        Rational,
        "both" if Rational else "",
        3,
        3,
        0,
        0,
        0,
        0,
        UKnots,
        UCounts,
        (0.0, 1.0),
        (3, 3),
        tuple(Poles),
        tuple(Weights) if Rational else (),
    )


def PillowFace(
    Edges: tuple[NurbsEdge, ...],
    Origin: tuple[int, int, int],
    UName: str,
    VName: str,
    Bulge: float,
    Weight: float,
    Split: bool,
) -> NurbsFace:
    UAxis, VAxis = KPillowAxes[UName], KPillowAxes[VName]
    Surface = PillowSurface(Origin, UName, VName, Bulge, Weight, Split)
    Corners = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    LoopUses: list[NurbsUse] = []
    for SideIndex in range(4):
        First, Second = Corners[SideIndex], Corners[(SideIndex + 1) % 4]
        EndIndices = tuple(
            CornerIndex(
                (
                    Origin[0]
                    + int(CornerPair[0]) * UAxis[0]
                    + int(CornerPair[1]) * VAxis[0],
                    Origin[1]
                    + int(CornerPair[0]) * UAxis[1]
                    + int(CornerPair[1]) * VAxis[1],
                    Origin[2]
                    + int(CornerPair[0]) * UAxis[2]
                    + int(CornerPair[1]) * VAxis[2],
                )
            )
            for CornerPair in (First, Second)
        )
        EdgeIndex = next(
            Index
            for Index, EdgeSpec in enumerate(Edges)
            if {EdgeSpec.StartVertex, EdgeSpec.EndVertex} == set(EndIndices)
        )
        Reverse = Edges[EdgeIndex].StartVertex != EndIndices[0]
        LeadCorner, TrailCorner = (Second, First) if Reverse else (First, Second)
        LoopUses.append(
            NurbsUse(EdgeIndex, Reverse, LinePcurve(LeadCorner, TrailCorner, 0.0, 1.0))
        )
    return NurbsFace(Surface, tuple(LoopUses))


def PillowBody() -> NurbsBody:
    Edges = PillowEdges()
    Points = tuple(
        CornerPoint((Index & 1, (Index >> 1) & 1, (Index >> 2) & 1))
        for Index in range(8)
    )
    Faces = tuple(PillowFace(Edges, *FaceSpec) for FaceSpec in KPillowFaces)
    return NurbsBody(Points, Edges, Faces)


def NurbsModels() -> tuple[tuple[str, NurbsBody], ...]:
    return (
        ("AuthoredPatch", PatchSheet(BicubicPatch())),
        ("AuthoredRational", PatchSheet(RationalPatch())),
        ("AuthoredPillow", PillowBody()),
    )
