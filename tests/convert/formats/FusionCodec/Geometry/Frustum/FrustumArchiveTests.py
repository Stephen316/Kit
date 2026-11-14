from math import pi as KCircleHalf
from pathlib import Path as FilePath

from pytest import approx as Approx, mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmb import EmitFrustumSmb
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from tests.convert.formats.FusionCodec.Geometry.Frustum.CheckConeLinks import (
    CheckConeLinks,
)
from tests.convert.formats.FusionCodec.Geometry.Frustum.ReadFrustum import ReadFrustum

KFrustumStamp = GeometryStamp("Kit", "Frustum integration", "2026-11-12T00:00:00Z")


@TestMarks.parametrize(
    "Lengths,BasePoint",
    (
        ((10.0, 14.0, 17.0), (20.0, -30.0, 5.0)),
        ((14.0, 8.0, 23.0), (-12.0, 7.0, -4.0)),
        ((9.0, 9.0, 11.0), (1.0, 2.0, 3.0)),
    ),
)
def TestFrustumFile(
    TmpPath: FilePath,
    Lengths: tuple[float, float, float],
    BasePoint: tuple[float, float, float],
) -> None:
    Target = TmpPath / "IndependentFrustum.smb"
    _ = Target.write_bytes(
        EmitFrustumSmb(FrustumBody(*Lengths, BasePoint), KFrustumStamp)
    )
    Evidence = ReadFrustum(Target.read_bytes())
    assert Evidence.Table.RootCount == 2
    CheckConeLinks(Evidence.Table)
    Bottom, Upper, Height = (Value / 10 for Value in Lengths)
    assert (Evidence.BottomRadius, Evidence.TopRadius, Evidence.Height) == Approx(
        (Bottom, Upper, Height)
    )
    Origin = Evidence.BasePoint
    assert (Origin.x, Origin.y, Origin.z) == Approx(
        tuple(Value / 10 for Value in BasePoint)
    )
    assert Evidence.ParamScale == Approx(Bottom)
    assert Evidence.SineAngle**2 + Evidence.CosineAngle**2 == Approx(1)
    assert Evidence.CosineAngle > 0
    assert Bottom + Height * Evidence.SineAngle / Evidence.CosineAngle == Approx(Upper)
    Volume = (
        KCircleHalf
        * Evidence.Height
        * (
            Evidence.BottomRadius**2
            + Evidence.BottomRadius * Evidence.TopRadius
            + Evidence.TopRadius**2
        )
        / 3
    )
    assert Volume == Approx(
        KCircleHalf * Height * (Bottom**2 + Bottom * Upper + Upper**2) / 3
    )


def TestFrustumTail() -> None:
    Payload = EmitFrustumSmb(FrustumBody(5.0, 9.0, 12.0, (0, 0, 0)), KFrustumStamp)
    with RaiseError(ValueError):
        _ = ReadFrustum(Payload + b"trailing")
