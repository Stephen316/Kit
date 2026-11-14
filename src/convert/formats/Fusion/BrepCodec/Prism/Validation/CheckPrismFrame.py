from math import dist as Distance

from convert.formats.Fusion.BrepCodec.Prism.Models.PrismFrame import PrismFrame
from convert.formats.Fusion.BrepCodec.Prism.Validation.CheckPrismEdge import (
    CheckPrismEdge,
)
from convert.formats.Fusion.BrepCodec.Prism.Validation.CheckPrismPlane import (
    CheckPrismPlane,
)
from convert.formats.Fusion.BrepCodec.Prism.Validation.PrismNumbers import CheckVector
from convert.formats.Fusion.GeometryCodec.Prism.CuboidBody import CuboidBody
from convert.formats.Fusion.GeometryCodec.Prism.CuboidCorners import CuboidCorners
from convert.formats.Fusion.GeometryCodec.Prism.PrismLayout import (
    KEdgeCorners,
    KFaceCorners,
)


def CheckPrismFrame(Model: CuboidBody, Frame: PrismFrame) -> None:
    Values = (
        Frame.CornersCm,
        Frame.FaceOrder,
        Frame.FaceStarts,
        Frame.FaceReverse,
        Frame.Edges,
        Frame.VertexOwners,
        Frame.Planes,
    )
    if any(
        type(Value) is not tuple or len(Value) != Count
        for Value, Count in zip(Values, (8, 6, 6, 6, 12, 8, 6), strict=True)
    ):
        raise ValueError("Prism history frame has an invalid field inventory")
    if sorted(Frame.FaceOrder) != list(range(6)) or any(
        type(Value) is not int for Value in Frame.FaceOrder
    ):
        raise ValueError("Invalid prism face chain")
    for Stored, Expected in zip(Frame.CornersCm, CuboidCorners(Model), strict=True):
        CheckVector(Stored)
        if Distance(Stored, tuple(Value / 10 for Value in Expected)) > 1e-8:
            raise ValueError("Prism history corners disagree with dimensions")
    for Index in range(6):
        if (
            type(Frame.FaceStarts[Index]) is not int
            or Frame.FaceStarts[Index] not in KFaceCorners[Index]
            or type(Frame.FaceReverse[Index]) is not bool
        ):
            raise ValueError("Invalid prism face loop start or sense")
        CheckPrismPlane(Frame, Index)
    for Index, EdgeValue in enumerate(Frame.Edges):
        CheckPrismEdge(EdgeValue, Index, Frame.CornersCm)
    for Corner, Owner in enumerate(Frame.VertexOwners):
        if (
            type(Owner) is not int
            or not 0 <= Owner < 12
            or Corner not in KEdgeCorners[Owner]
        ):
            raise ValueError("Prism vertex owner edge is not incident")
