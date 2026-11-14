from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks

from convert.formats.Fusion.BrepCodec.Frustum.EmitFrustumHist import EmitFrustumHist
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
from tests.convert.formats.FusionCodec.Brep.Frustum.FrustumArchive import FrustumArchive
from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
def TestRolledCone(TmpPath: FilePath) -> None:
    Native = ReadFrustumHist(
        NativeHistory("re/Fusion/Study/timeline-5867579925b5/rolled_back.f3d")
    )
    assert Native.History.CurrentStateId == Native.History.CurrentId == 3
    assert Native.History.MaxStateId == 10
    assert Native.History.NextEntityTag == 6
    assert Native.History.InitialId == 2
    assert Native.History.BoardStatus == 2
    Payload = EmitFrustumHist(
        Native.Model,
        Native.Identity,
        Native.TagSet,
        Native.History,
        Native.Stamp,
        Native.Frame,
    )
    Parsed = FrustumArchive(TmpPath / "RolledReconstruction.zip", Payload)
    assert Parsed == Native
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
