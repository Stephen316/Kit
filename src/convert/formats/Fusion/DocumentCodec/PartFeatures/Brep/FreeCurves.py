from math import cos as Cosine, pi as KHalfTurn, sin as SineOf

from convert.formats.Fusion.BrepCodec.Journal.Geometry.EllipseNode import EllipseNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.StraightNode import StraightNode
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.FreeEdge import FreeEdge
from convert.formats.Fusion.DocumentCodec.PartFeatures.Brep.SpaceMath import (
    AddVector,
    CrossProduct,
    KSpaceVector,
    ScaleVector,
    SubVector,
    UnitVector,
    VectorLength,
)


def LineEdge(Start: KSpaceVector, Finish: KSpaceVector) -> FreeEdge:
    Reach = VectorLength(SubVector(Finish, Start))
    Heading = UnitVector(SubVector(Finish, Start))
    Curve = StraightNode(EntityPrefix(-1, -1), Start, Heading, 0.0, Reach)
    return FreeEdge(Curve, 0.0, Reach, Start, Finish)


def ArcEdge(
    Center: KSpaceVector,
    Normal: KSpaceVector,
    Start: KSpaceVector,
    Sweep: float,
    Finish: KSpaceVector,
) -> FreeEdge:
    Offset = SubVector(Start, Center)
    Radius = VectorLength(Offset)
    Leading = UnitVector(Offset)
    SideVector = CrossProduct(Normal, Leading)
    HalfSweep = Sweep / 2.0
    Middle = AddVector(
        ScaleVector(Leading, Cosine(HalfSweep)),
        ScaleVector(SideVector, SineOf(HalfSweep)),
    )
    Major = ScaleVector(Middle, Radius)
    Curve = EllipseNode(EntityPrefix(-1, -1), Center, Normal, Major, 1.0, None, None)
    return FreeEdge(Curve, 0.0 - HalfSweep, HalfSweep, Start, Finish)


def EllipseEdge(
    Center: KSpaceVector, Start: KSpaceVector, Finish: KSpaceVector
) -> FreeEdge:
    Minor = SubVector(Start, Center)
    Major = SubVector(Finish, Center)
    Normal = UnitVector(CrossProduct(Minor, Major))
    Ratio = VectorLength(Minor) / VectorLength(Major)
    Curve = EllipseNode(EntityPrefix(-1, -1), Center, Normal, Major, Ratio, None, None)
    return FreeEdge(Curve, 0.0 - KHalfTurn / 2.0, 0.0, Start, Finish)
