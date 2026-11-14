from convert.formats.Fusion.BrepCodec.Prism.Models.PrismEdge import PrismEdge
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismLine import PrismLine
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismPlane import PrismPlane
from convert.formats.Fusion.GeometryCodec.Prism.BuildUses import BuildUses
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.formats.Fusion.GeometryCodec.Prism.CuboidCorners import CuboidCorners
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFaceCorners,
)
from convert.formats.Fusion.GeometryCodec.Prism.PrismPlanes import KFaceFrames


def FreshPrism(Model: CuboidBody) -> PrismFrame:
    Corners = tuple(
        (Point[0] / 10, Point[1] / 10, Point[2] / 10) for Point in CuboidCorners(Model)
    )
    Owners = {Value.EdgeIndex: Value.FaceIndex for Value in BuildUses()}
    Edges = tuple(
        PrismEdge(
            Start,
            Finish,
            0.0,
            1.0,
            Owners[Index],
            PrismLine(
                Corners[Start],
                (
                    Corners[Finish][0] - Corners[Start][0],
                    Corners[Finish][1] - Corners[Start][1],
                    Corners[Finish][2] - Corners[Start][2],
                ),
            ),
        )
        for Index, (Start, Finish) in enumerate(KEdgeCorners)
    )
    VertexOwners = {
        Corner: Index
        for Index, CornersPair in enumerate(KEdgeCorners)
        for Corner in CornersPair
    }
    Planes = tuple(
        PrismPlane(Corners[Indices[0]], Normal, Basis)
        for Indices, (Normal, Basis) in zip(KFaceCorners, KFaceFrames, strict=True)
    )
    return PrismFrame(
        Corners,
        tuple(range(6)),
        tuple(Value[0] for Value in KFaceCorners),
        (False,) * 6,
        Edges,
        tuple(VertexOwners[Index] for Index in range(8)),
        Planes,
    )
