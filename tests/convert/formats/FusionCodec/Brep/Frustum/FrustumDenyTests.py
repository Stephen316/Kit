from dataclasses import replace as Replace
from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.Writing.FreshFrustum import FreshFrustum
from convert.formats.Fusion.GeometryCodec.Frustum.FrustumBody import FrustumBody
from tests.convert.formats.FusionCodec.Brep.Frustum.FrustumArchive import FrustumArchive
from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory
from tests.convert.formats.FusionCodec.Brep.SampleInputs import MakeSample


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize(
    "SourcePath",
    (
        "re/Fusion/Study/moretools-88a2cd6cad0b/Draft.f3d",
        "re/Fusion/Study/faceedits-3f120cbee8d9/offset_cylinder.f3d",
    ),
)
def TestJournalDeny(SourcePath: str) -> None:
    with RaiseError(ValueError):
        _ = ReadFrustumHist(NativeHistory(SourcePath))


@TestMarks.parametrize(
    "Failure", ("axis", "angle", "scale", "normal", "orientation", "point", "owner")
)
def TestFrameReject(TmpPath: FilePath, Failure: str) -> None:
    Sample = MakeSample()
    Model = FrustumBody(12.5, 17.0, 21.75, (3.0, -4.0, 5.0))
    Frame = FreshFrustum(Model)
    Invalid = {
        "axis": Replace(Frame, Surface=Replace(Frame.Surface, Axis=(1.0, 0.0, 0.0))),
        "angle": Replace(
            Frame, Surface=Replace(Frame.Surface, SineAngle=-Frame.Surface.SineAngle)
        ),
        "scale": Replace(Frame, Surface=Replace(Frame.Surface, ScaleCm=0.0)),
        "normal": Replace(Frame, Upper=Replace(Frame.Upper, Normal=(0.0, 1.0, 0.0))),
        "orientation": Replace(
            Frame, Upper=Replace(Frame.Upper, CapReverse=Frame.Upper.SideReverse)
        ),
        "point": Replace(Frame, Upper=Replace(Frame.Upper, PointCm=(0.0, 0.0, 0.0))),
        "owner": Replace(Frame, Upper=Replace(Frame.Upper, VertexIndex=1)),
    }
    with RaiseError(ValueError):
        Payload = EmitFrustumHist(
            Model,
            Sample.Identity,
            Sample.TagSet,
            Sample.History,
            Sample.Stamp,
            Invalid[Failure],
        )
        _ = FrustumArchive(TmpPath / "Rejected.zip", Payload)
    assert not (TmpPath / "Rejected.zip").exists()


def TestHistoryTail(TmpPath: FilePath) -> None:
    Sample = MakeSample()
    Model = FrustumBody(12.5, 17.0, 21.75, (3.0, -4.0, 5.0))
    Payload = EmitFrustumHist(
        Model, Sample.Identity, Sample.TagSet, Sample.History, Sample.Stamp
    )
    with RaiseError(ValueError):
        _ = FrustumArchive(TmpPath / "Trailing.zip", Payload + b"trailing")
