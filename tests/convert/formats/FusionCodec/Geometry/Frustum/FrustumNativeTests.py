from math import cos as Cosine, pi as KHalfCircle, sin as SineValue
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.GeometryCodec.Frustum.EmitFrustumSmb import EmitFrustumSmb
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from tests.convert.formats.FusionCodec.Geometry.Frustum.ReadFrustum import ReadFrustum

KRepoRoot = FilePath(__file__).resolve().parents[6]


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestNativeTaper(TmpPath: FilePath) -> None:
    Source = KRepoRoot / "re/Fusion/Study/extents-f0f33a9a605f/taper.f3d"
    with ZipFile(Source) as Archive:
        Names = tuple(
            NameValue for NameValue in Archive.namelist() if NameValue.endswith(".smbh")
        )
        assert len(Names) == 1
        Native = ReadFrustum(Archive.read(Names[0]))
    assert (Native.BottomRadius, Native.TopRadius, Native.Height) == Approx(
        (1.0, 1.2087337535349378, 1.7)
    )
    Angle = 7 * KHalfCircle / 180
    assert (Native.SineAngle, Native.CosineAngle, Native.ParamScale) == Approx(
        (SineValue(Angle), Cosine(Angle), 1.0)
    )
    Origin = Native.BasePoint
    Model = FrustumBody(
        Native.BottomRadius * 10,
        Native.TopRadius * 10,
        Native.Height * 10,
        (Origin.x * 10, Origin.y * 10, Origin.z * 10),
    )
    Stamp = GeometryStamp("Kit", "Native frustum compatibility", "2026-11-12T00:00:00Z")
    Target = TmpPath / "RebuiltNativeFrustum.smb"
    _ = Target.write_bytes(EmitFrustumSmb(Model, Stamp))
    Parsed = ReadFrustum(Target.read_bytes())
    assert (Parsed.BottomRadius, Parsed.TopRadius, Parsed.Height) == Approx(
        (Native.BottomRadius, Native.TopRadius, Native.Height)
    )
    assert (Parsed.SineAngle, Parsed.CosineAngle, Parsed.ParamScale) == Approx(
        (Native.SineAngle, Native.CosineAngle, Native.ParamScale)
    )
