from math import cos as Cosine, pi as KHalfCircle, sin as SineValue, tan as Tangent
from pathlib import Path as FilePath
from struct import pack as PackValue
from sys import version_info as PythonVersion

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
from tests.convert.formats.FusionCodec.Brep.Frustum.FrustumArchive import FrustumArchive
from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize(
    "SourcePath,Height,Degrees",
    (
        ("re/Fusion/Study/extents-f0f33a9a605f/taper.f3d", 17.0, 7.0),
        ("re/Fusion/Study/holdouts-f8c508a73323/drafted_extrusion.f3d", 21.25, 5.0),
    ),
)
def TestNativeCone(
    TmpPath: FilePath, SourcePath: str, Height: float, Degrees: float
) -> None:
    Native = ReadFrustumHist(NativeHistory(SourcePath))
    Angle = Degrees * KHalfCircle / 180
    assert (
        Native.Model.BottomRadius,
        Native.Model.TopRadius,
        Native.Model.Height,
    ) == Approx((10.0, 10.0 + Height * Tangent(Angle), Height))
    assert (
        Native.Frame.Surface.SineAngle,
        Native.Frame.Surface.CosineAngle,
        Native.Frame.Surface.ScaleCm,
    ) == Approx((SineValue(Angle), Cosine(Angle), 1.0))
    assert Native.Frame.Upper.Normal == (0.0, 0.0, -1.0)
    assert not Native.Frame.Upper.SideReverse
    assert Native.Frame.Upper.CapReverse
    assert (Native.Frame.Upper.VertexIndex, Native.Frame.Lower.VertexIndex) == (2, 0)
    assert Native.Identity.OperationId == 301
    assert Native.Identity.SecondaryId == 4
    assert (Native.History.InitialId, Native.History.CurrentId) == (2, 4)
    Payload = EmitFrustumHist(
        Native.Model,
        Native.Identity,
        Native.TagSet,
        Native.History,
        Native.Stamp,
        Native.Frame,
    )
    Parsed = FrustumArchive(TmpPath / "NativeReconstruction.zip", Payload)
    assert Parsed == Native
    assert PackValue("<3d", *Parsed.Frame.Upper.PointCm) == PackValue(
        "<3d", *Native.Frame.Upper.PointCm
    )
    assert (
        EmitFrustumHist(
            Parsed.Model,
            Parsed.Identity,
            Parsed.TagSet,
            Parsed.History,
            Parsed.Stamp,
            Parsed.Frame,
        )
        == Payload
    )
