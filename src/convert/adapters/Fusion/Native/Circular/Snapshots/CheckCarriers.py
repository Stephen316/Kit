from convert.adapters.Fusion.Native.Graph.GraphChecks import SameNumbers
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PlaneNode import PlaneNode
from convert.formats.Fusion.BrepCodec.Journal.Geometry.ConeNode import ConeNode
from convert.formats.Fusion.BrepCodec.Frustum.Models.ConeFrame import ConeFrame
from convert.formats.Fusion.BrepCodec.Frustum.Validation.CheckConeFrame import (
    CheckConeFrame,
)
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody


def CheckPlane(Plane: PlaneNode, Center: tuple[float, float, float]) -> None:
    SameNumbers(Plane.OriginCm, Center)
    SameNumbers(Plane.Normal, (0.0, 0.0, 1.0))
    SameNumbers(Plane.ReferenceAxis, (1.0, 0.0, 0.0))
    if Plane.ReversedV or any(
        Value is not None
        for Value in (Plane.ULower, Plane.UUpper, Plane.VLower, Plane.VUpper)
    ):
        raise ValueError(
            "Native circular snapshot plane has unsupported orientation or bounds"
        )


def CheckCone(Surface: ConeNode, Model: FrustumBody) -> None:
    if any(
        Value is not None
        for Value in (
            Surface.EllipseLower,
            Surface.EllipseUpper,
            Surface.ULower,
            Surface.UUpper,
            Surface.VLower,
            Surface.VUpper,
        )
    ):
        raise ValueError(
            "Native circular snapshot cone must have unbounded carrier parameters"
        )
    CheckConeFrame(
        Model,
        ConeFrame(
            Surface.OriginCm,
            Surface.AxisVector,
            Surface.MajorAxisCm,
            Surface.EllipseRatio,
            Surface.SineAngle,
            Surface.CosineAngle,
            Surface.UScaleCm,
            Surface.Reversed,
        ),
    )
