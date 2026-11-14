from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import approx as Approx, mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.PermuteJournal import PermuteJournal
from convert.formats.Fusion.BrepCodec.Journal.Planar.ReadPlanarState import (
    ReadPlanarState,
)
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize(
    "SourcePath,FaceCount,VertexCount,Volume,BodyTag",
    (
        ("re/Fusion/Study/meshconverts-4b42d39fb1d5/faceted_closed.f3d", 4, 4, 4.0, 30),
        (
            "re/Fusion/Study/pipemodes-87cfa7d8d82b/triangular.f3d",
            5,
            6,
            1.2470765814495919,
            0,
        ),
    ),
)
def TestNativePoly(
    TmpPath: FilePath,
    SourcePath: str,
    FaceCount: int,
    VertexCount: int,
    Volume: float,
    BodyTag: int,
) -> None:
    Payload = NativeHistory(SourcePath)
    Native = ReadJournal(Payload)
    assert EmitJournal(Native) == Payload
    Order = (
        0,
        *reversed(range(1, Native.ActiveCount)),
        *reversed(range(Native.ActiveCount, len(Native.Entities))),
    )
    Changed = PermuteJournal(Native, Order)
    Encoded = EmitJournal(Changed)
    Parsed = JournalArchive(TmpPath / "PlanarNative.zip", Encoded)
    assert Encoded != Payload
    Bodies = ReadPlanarState(Parsed)
    assert len(Bodies) == 1
    assert len(Bodies[0].FaceRefs) == FaceCount
    assert len(Bodies[0].PointsCm) == VertexCount
    assert Bodies[0].VolumeCm3 == Approx(Volume)
    assert Bodies[0].EntityTag == BodyTag
    assert ReadPlanarState(Parsed, 2) == ()
