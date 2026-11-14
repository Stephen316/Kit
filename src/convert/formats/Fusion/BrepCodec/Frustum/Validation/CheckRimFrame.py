from math import cos as Cosine, sin as SineValue

from convert.formats.Fusion.BrepCodec.Frustum.Models.RimFrame import RimFrame
from convert.formats.Fusion.BrepCodec.Frustum.Validation.CheckRimFields import (
    CheckRimFields,
)
from convert.formats.Fusion.BrepCodec.Frustum.Validation.FrustumNumbers import (
    IsNear,
    IsNearVector,
)
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def CheckRimFrame(Model: FrustumBody, Frame: RimFrame, IsUpper: bool) -> None:
    CheckRimFields(Frame)
    Radius = (Model.TopRadius if IsUpper else Model.BottomRadius) / 10
    Origin = Model.BasePoint
    Center = (
        Origin[0] / 10,
        Origin[1] / 10,
        (Origin[2] + (Model.Height if IsUpper else 0)) / 10,
    )
    if not IsNear(Frame.MajorVectorCm[0], Radius) or not IsNearVector(
        Frame.CenterCm, Center
    ):
        raise ValueError("Frustum rim dimensions disagree with its body")
    if not IsNearVector(Frame.PlaneOriginCm, Frame.CenterCm):
        raise ValueError("Frustum cap plane misses its boundary")
    SeamPoint = (
        Frame.CenterCm[0] + Radius * Cosine(Frame.EdgeStart),
        Frame.CenterCm[1] + Radius * SineValue(Frame.EdgeStart) * Frame.Normal[2],
        Frame.CenterCm[2],
    )
    if not IsNearVector(Frame.PointCm, SeamPoint):
        raise ValueError("Frustum seam vertex misses its circular boundary")
    ExpectedSide = IsUpper if Frame.Normal[2] > 0 else not IsUpper
    if Frame.SideReverse != ExpectedSide or Frame.CapReverse == Frame.SideReverse:
        raise ValueError("Frustum boundary orientation is inconsistent")
