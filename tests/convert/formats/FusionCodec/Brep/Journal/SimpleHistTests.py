from pathlib import Path as FilePath
from sys import version_info as PythonVersion

from pytest import mark as TestMarks

from convert.formats.Fusion.BrepCodec.Journal.EmitJournal import EmitJournal
from convert.formats.Fusion.BrepCodec.Journal.Materialize import Materialize
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from tests.convert.formats.FusionCodec.Brep.Frustum.NativeHistory import NativeHistory
from tests.convert.formats.FusionCodec.Brep.Journal.JournalArchive import JournalArchive


@TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)
@TestMarks.parametrize(
    "SourcePath,EntityCount",
    (
        ("re/Fusion/Study/timeline-5867579925b5/rolled_back.f3d", 35),
        (
            "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
            102,
        ),
    ),
)
def TestSimpleHist(TmpPath: FilePath, SourcePath: str, EntityCount: int) -> None:
    Payload = NativeHistory(SourcePath)
    Native = ReadJournal(Payload)
    assert len(Native.Entities) == Native.ActiveCount == EntityCount
    assert len(Native.States) == 2
    assert tuple(len(State.Versions) for State in Materialize(Native)) == (
        EntityCount,
        1,
    )
    assert EmitJournal(Native) == Payload
    Parsed = JournalArchive(TmpPath / "SimpleHistory.zip", EmitJournal(Native))
    assert Parsed == Native
