from math import cos as Cosine, hypot as Hypotenuse, pi as KHalfTurn, radians as Radians
from math import sin as SineOf

from convert.formats.Fusion.DocumentCodec.Model.AuthorState import AuthorState
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.ArcCurve import ArcCurve
from convert.formats.Fusion.DocumentCodec.PartFeatures.Model.LineCurve import (
    LineCurve,
)
from convert.formats.Fusion.DocumentCodec.PartFeatures.Profile.SketchPlan import (
    SketchEdge,
    SketchPlan,
)
from convert.formats.Fusion.DocumentCodec.Values.MakeAttributes import MakeAttributes
from convert.formats.Fusion.DocumentCodec.Values.ValueShapes import MakePoint


def PointRole(Prefix: str, Index: int | None) -> str | None:
    return None if Index is None else Prefix + "point" + str(Index)


def LineFields(
    Author: AuthorState, Prefix: str, Segment: SketchEdge
) -> dict[str, object]:
    Curve = Segment.Curve
    if not isinstance(Curve, LineCurve):
        raise ValueError("Fusion sketch line fields require a line")
    StartX, StartY = Curve.StartMm[0] / 10.0, Curve.StartMm[1] / 10.0
    DeltaX, DeltaY = (
        Curve.FinishMm[0] / 10.0 - StartX,
        Curve.FinishMm[1] / 10.0 - StartY,
    )
    Length = Hypotenuse(DeltaX, DeltaY)
    return dict(
        lineCurve=dict(
            startPoint=MakePoint(StartX, StartY), displacement=MakePoint(DeltaX, DeltaY)
        ),
        lineDirection=MakePoint(DeltaX / Length, DeltaY / Length),
        planeNormal=MakePoint(0.0, 0.0, 1.0),
        rStartPoint=Author.Reference(PointRole(Prefix, Segment.StartIndex)),
        rEndPoint=Author.Reference(PointRole(Prefix, Segment.FinishIndex)),
    )


def ArcFields(
    Author: AuthorState, Prefix: str, Segment: SketchEdge
) -> dict[str, object]:
    Curve = Segment.Curve
    if isinstance(Curve, LineCurve):
        raise ValueError("Fusion sketch arc fields require an arc or circle")
    Start, Sweep = 0.0, 2.0 * KHalfTurn
    if isinstance(Curve, ArcCurve):
        Start, Sweep = Radians(Curve.StartDegrees), Radians(Curve.SweepDegrees)
    return dict(
        arcCurve=dict(
            center=MakePoint(Curve.CenterMm[0] / 10.0, Curve.CenterMm[1] / 10.0),
            normal=MakePoint(0.0, 0.0, 1.0),
            refVec=MakePoint(Cosine(Start) + 0.0, SineOf(Start) + 0.0),
            radius=Curve.RadiusMm / 10.0,
            startAngle=0.0,
            endAngle=Sweep,
        ),
        rCenterPoint=Author.Reference(PointRole(Prefix, Segment.CenterIndex)),
        rStartPoint=Author.Reference(PointRole(Prefix, Segment.StartIndex)),
        rEndPoint=Author.Reference(PointRole(Prefix, Segment.FinishIndex)),
    )


def AddSketchGeom(Author: AuthorState, Prefix: str, Sketched: SketchPlan) -> None:
    Generation = Author.Policy.SketchGeneration
    for Index, PointCm in enumerate(Sketched.PointsCm):
        RoleName = Prefix + "point" + str(Index)
        Author.Allocate(
            RoleName,
            "Point3D",
            ParentRole=Prefix + "sketch",
            Fields={"point": MakePoint(*PointCm)},
            NamedPairs=MakeAttributes(
                EntityGenesis=Generation, pt_tag=Sketched.PointTags[Index]
            ),
        )
        Author.Allocate(RoleName + "_uses", "CurveUses", ParentRole=RoleName)
        Author.Change(RoleName, curveUses=Author.Reference(RoleName + "_uses"))
    for Index, Segment in enumerate(Sketched.Edges):
        IsLine = isinstance(Segment.Curve, LineCurve)
        Author.Allocate(
            Prefix + "curve" + str(Index),
            "Line3D" if IsLine else "CircArc3D",
            ParentRole=Prefix + "sketch",
            Fields=(LineFields if IsLine else ArcFields)(Author, Prefix, Segment),
            NamedPairs=MakeAttributes(
                EntityGenesis=Generation,
                crv_primary_id=Segment.CurveTag,
                crv_secondary_id=0,
            ),
        )
    LinkPointUses(Author, Prefix, Sketched)


def LinkPointUses(Author: AuthorState, Prefix: str, Sketched: SketchPlan) -> None:
    for Index in range(len(Sketched.PointsCm)):
        Users = [
            Author.Reference(Prefix + "curve" + str(Ordinal))
            for Ordinal, Segment in enumerate(Sketched.Edges)
            if Index in (Segment.StartIndex, Segment.FinishIndex, Segment.CenterIndex)
        ]
        Author.Change(Prefix + "point" + str(Index) + "_uses", geometries=Users)
