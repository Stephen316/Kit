from convert.formats.Fusion.BrepCodec.Journal.Geometry.EntityPrefix import EntityPrefix
from convert.formats.Fusion.BrepCodec.Journal.Geometry.FaceNode import FaceNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.LoopNode import LoopNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Planar.VectorMath import (
    CrossProduct,
    Normalize,
    Subtract,
)
from convert.formats.Fusion.BrepCodec.Journal.PolyAuthor.PolyLayout import PolyLayout


def MakePolyFaces(Layout: PolyLayout) -> tuple[FaceNode, ...]:
    return tuple(
        FaceNode(
            EntityPrefix(-1, -1),
            Layout.FaceBase + Index + 1 if Index + 1 < len(Layout.FaceLoops) else -1,
            Layout.LoopBase + Index,
            3,
            Layout.PlaneBase + Index,
            False,
            False,
            None,
        )
        for Index in range(len(Layout.FaceLoops))
    )


def MakePolyLoops(Layout: PolyLayout) -> tuple[LoopNode, ...]:
    return tuple(
        LoopNode(
            EntityPrefix(-1, -1),
            -1,
            Layout.CoedgeBase + Offset,
            Layout.FaceBase + Index,
        )
        for Index, Offset in enumerate(Layout.LoopStarts)
    )


def MakePolyPlanes(Layout: PolyLayout) -> tuple[PlaneNode, ...]:
    Results: list[PlaneNode] = []
    for RingValue in Layout.FaceLoops:
        Origin = Layout.PointsCm[RingValue[0]]
        Along = Subtract(Layout.PointsCm[RingValue[1]], Origin)
        Across = Subtract(Layout.PointsCm[RingValue[2]], Origin)
        Normal = Normalize(CrossProduct(Along, Across))
        Results.append(
            PlaneNode(
                EntityPrefix(-1, -1),
                Origin,
                Normal,
                Normalize(Along),
                False,
                None,
                None,
                None,
                None,
            )
        )
    return tuple(Results)
